"""
Automaton Auditor — LangGraph StateGraph Definition
Implements the full Digital Courtroom architecture with:
- Fan-Out: Detectives run in parallel (RepoInvestigator, DocAnalyst, VisionInspector)
- Fan-In: EvidenceAggregator synchronizes before Judicial layer
- Fan-Out: Judges run in parallel (Prosecutor, Defense, TechLead)
- Fan-In: ChiefJustice synthesizes final verdict and serializes Markdown report
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from src.state import AgentState
from src.nodes.detectives import (
    doc_analyst_node,
    evidence_aggregator_node,
    repo_investigator_node,
    vision_inspector_node,
)
from src.nodes.judges import (
    prosecutor_node,
    defense_node,
    tech_lead_node,
)
from src.nodes.justice import chief_justice_node
from src.tools.repo_tools import validate_repo_url

# Load environment variables from .env
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rubric Loading
# ---------------------------------------------------------------------------

def load_rubric(rubric_path: str = "rubric.json") -> list:
    """Load the machine-readable rubric from rubric.json."""
    rubric_file = Path(rubric_path)
    if not rubric_file.exists():
        logger.warning(f"Rubric not found at {rubric_path}, using empty rubric.")
        return []
    with open(rubric_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("dimensions", [])


# ---------------------------------------------------------------------------
# Graph Entry Node: Context Builder
# ---------------------------------------------------------------------------

def context_builder_node(state: AgentState) -> Dict[str, Any]:
    """
    Initializes the audit by loading the rubric and setting up initial state.
    Validates the repo URL before fan-out to detectives.
    This is the START node that prepares context before fan-out to detectives.
    """
    rubric_dims = load_rubric()
    repo_url = state["repo_url"]

    # Validate URL upfront — sets error flag if invalid
    is_valid, validation_msg = validate_repo_url(repo_url)
    errors = [] if is_valid else [f"Invalid repository URL: {validation_msg}"]

    logger.info(
        f"[ContextBuilder] Loaded {len(rubric_dims)} rubric dimensions. "
        f"Target repo: {repo_url} | URL valid: {is_valid}"
    )
    print(f"\n{'='*60}")
    print(f"AUTOMATON AUDITOR — Digital Courtroom")
    print(f"{'='*60}")
    print(f"  Target Repo: {repo_url}")
    print(f"  URL Valid:   {'✓' if is_valid else '✗ ' + validation_msg}")
    print(f"  PDF Report:  {state.get('pdf_path', 'N/A')}")
    print(f"  Rubric Dims: {len(rubric_dims)}")
    print(f"{'='*60}\n")

    return {
        "rubric_dimensions": rubric_dims,
        "evidences": {},
        "opinions": [],
        "errors": errors,
        "final_report": None,
        # output_dir is set in initial_state — don't return it here
        # (returning plain str fields from parallel nodes causes merge conflicts)
    }


def error_handler_node(state: AgentState) -> Dict[str, Any]:
    """
    Handles unrecoverable errors (e.g., invalid repo URL, network failure).
    Produces a partial report with error information instead of crashing.
    """
    errors = state.get("errors", [])
    repo_url = state.get("repo_url", "unknown")
    logger.error(f"[ErrorHandler] Routing to error handler. Errors: {errors}")

    print(f"\n{'='*60}")
    print(f"ERROR HANDLER — Partial Report")
    print(f"{'='*60}")
    for err in errors:
        print(f"  ✗ {err}")
    print(f"{'='*60}\n")

    return {
        "errors": [f"Audit terminated early. Repo: {repo_url}. Errors: {'; '.join(errors)}"],
    }


def route_after_context(state: AgentState) -> List[str]:
    """
    Conditional routing after ContextBuilder.
    If URL is invalid → ErrorHandler (single node).
    Otherwise → fan-out to all 3 detectives in parallel.

    Returns a list of node names for LangGraph to execute in parallel.
    """
    errors = state.get("errors", [])
    if errors:
        return ["ErrorHandler"]
    # Parallel fan-out: LangGraph executes all three simultaneously
    return ["RepoInvestigator", "DocAnalyst", "VisionInspector"]


# ---------------------------------------------------------------------------
# Graph Construction
# ---------------------------------------------------------------------------

def build_graph() -> Any:
    """
    Build and compile the full Automaton Auditor StateGraph.

    Architecture:
        START
          │
          ▼
    ContextBuilder ──[invalid URL]──► ErrorHandler ──► END
          │ [valid URL — parallel fan-out]
    ┌─────┼──────────────┐
    ▼     ▼              ▼
    Repo  Doc        Vision
    Inv.  Analyst    Inspector
    └─────┼──────────────┘
          ▼ [fan-in]
    EvidenceAggregator
          │ [parallel fan-out]
    ┌─────┼──────────────┐
    ▼     ▼              ▼
    Pros- Defense    TechLead
    ecutor
    └─────┼──────────────┘
          ▼ [fan-in]
    ChiefJustice
          │
         END
    """
    builder = StateGraph(AgentState)

    # --- Add Nodes ---
    builder.add_node("ContextBuilder", context_builder_node)
    builder.add_node("ErrorHandler", error_handler_node)
    builder.add_node("RepoInvestigator", repo_investigator_node)
    builder.add_node("DocAnalyst", doc_analyst_node)
    builder.add_node("VisionInspector", vision_inspector_node)
    builder.add_node("EvidenceAggregator", evidence_aggregator_node)
    builder.add_node("Prosecutor", prosecutor_node)
    builder.add_node("Defense", defense_node)
    builder.add_node("TechLead", tech_lead_node)
    builder.add_node("ChiefJustice", chief_justice_node)

    # --- Wire Edges ---

    # START → ContextBuilder
    builder.add_edge(START, "ContextBuilder")

    # ContextBuilder → conditional fan-out:
    #   invalid URL → [ErrorHandler]
    #   valid URL   → [RepoInvestigator, DocAnalyst, VisionInspector] (parallel)
    builder.add_conditional_edges(
        "ContextBuilder",
        route_after_context,
    )

    # ErrorHandler → END (graceful failure)
    builder.add_edge("ErrorHandler", END)

    # All 3 Detectives → EvidenceAggregator [Fan-In]
    builder.add_edge("RepoInvestigator", "EvidenceAggregator")
    builder.add_edge("DocAnalyst", "EvidenceAggregator")
    builder.add_edge("VisionInspector", "EvidenceAggregator")

    # EvidenceAggregator → Judges [Fan-Out — parallel]
    builder.add_edge("EvidenceAggregator", "Prosecutor")
    builder.add_edge("EvidenceAggregator", "Defense")
    builder.add_edge("EvidenceAggregator", "TechLead")

    # All 3 Judges → ChiefJustice [Fan-In]
    builder.add_edge("Prosecutor", "ChiefJustice")
    builder.add_edge("Defense", "ChiefJustice")
    builder.add_edge("TechLead", "ChiefJustice")

    # ChiefJustice → END
    builder.add_edge("ChiefJustice", END)

    # Compile the graph
    graph = builder.compile()
    logger.info("[GraphBuilder] Full Digital Courtroom graph compiled successfully.")
    return graph


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def run_audit(repo_url: str, pdf_path: str = "", output_dir: str = "audit") -> Dict[str, Any]:
    """
    Run the full Automaton Auditor swarm against a target repo and PDF report.

    Args:
        repo_url:   GitHub repository URL to audit
        pdf_path:   Path to the PDF architectural report (optional but recommended)
        output_dir: Directory where the Markdown audit report will be written

    Returns:
        Final AgentState with all evidence, opinions, and the final AuditReport
    """
    graph = build_graph()

    initial_state: AgentState = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "output_dir": output_dir,
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "errors": [],
        "final_report": None,
    }

    logger.info(f"[Audit] Starting full Digital Courtroom audit of: {repo_url}")
    result = graph.invoke(initial_state)
    logger.info("[Audit] Complete.")
    return result


# Backwards-compatible alias
run_detective_audit = run_audit


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.graph <repo_url> [pdf_path] [output_dir]")
        print("Example: python -m src.graph https://github.com/user/repo reports/interim_report.pdf audit/")
        sys.exit(1)

    repo_url = sys.argv[1]
    pdf_path = sys.argv[2] if len(sys.argv) > 2 else ""
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "audit"

    result = run_audit(repo_url, pdf_path, output_dir)

    # Print evidence summary
    print("\n" + "="*60)
    print("EVIDENCE SUMMARY")
    print("="*60)
    evidences = result.get("evidences", {})
    for detective, evs in evidences.items():
        print(f"\n[{detective.upper()} DETECTIVE — {len(evs)} items]")
        for ev in evs:
            status = "✓ FOUND" if ev.found else "✗ NOT FOUND"
            print(f"  {status} | {ev.goal} | confidence={ev.confidence:.2f}")
            print(f"    Location: {ev.location}")
            if ev.rationale:
                print(f"    Rationale: {ev.rationale[:150]}...")

    # Print opinions summary
    opinions = result.get("opinions", [])
    if opinions:
        print(f"\n{'='*60}")
        print(f"JUDICIAL OPINIONS — {len(opinions)} total")
        print("="*60)
        by_criterion: Dict[str, Any] = {}
        for op in opinions:
            by_criterion.setdefault(op.criterion_id, []).append(op)
        for crit_id, ops in by_criterion.items():
            scores = {op.judge: op.score for op in ops}
            print(f"  {crit_id}: {scores}")

    # Print final report summary
    final_report = result.get("final_report")
    if final_report:
        print(f"\n{'='*60}")
        print(f"FINAL VERDICT")
        print("="*60)
        print(f"  Overall Score: {final_report.overall_score:.1f} / 5.0")
        print(f"  Executive Summary:\n{final_report.executive_summary}")
        print(f"\n  Audit report written to: audit/audit_report.md")

    errors = result.get("errors", [])
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for err in errors:
            print(f"  ✗ {err}")
