"""
Automaton Auditor — LangGraph StateGraph Definition
Implements the full Digital Courtroom architecture with:
- Fan-Out: Detectives run in parallel (RepoInvestigator, DocAnalyst, VisionInspector)
- Fan-In: EvidenceAggregator synchronizes before Judicial layer
- Fan-Out: Judges run in parallel (Prosecutor, Defense, TechLead) [Phase 2]
- Fan-In: ChiefJustice synthesizes final verdict [Phase 2]

INTERIM VERSION: Detective layer + EvidenceAggregator fully wired.
Judicial layer stubs present but not yet invoked.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from langgraph.constants import Send

from src.state import AgentState
from src.nodes.detectives import (
    doc_analyst_node,
    evidence_aggregator_node,
    repo_investigator_node,
    vision_inspector_node,
)
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


def route_after_context(state: AgentState) -> str:
    """
    Conditional routing after ContextBuilder.
    If URL is invalid → ErrorHandler.
    Otherwise → fan-out to all 3 detectives (LangGraph handles parallel edges).
    """
    errors = state.get("errors", [])
    if errors:
        return "error"
    return "ok"


# ---------------------------------------------------------------------------
# Graph Construction
# ---------------------------------------------------------------------------

def build_graph() -> Any:
    """
    Build and compile the Automaton Auditor StateGraph.

    Architecture:
        START
          │
          ▼
    ContextBuilder ──[invalid URL]──► ErrorHandler ──► END
          │ [valid URL]
    ┌─────┼─────────────┐
    ▼     ▼             ▼
    Repo  Doc       Vision
    Inv.  Analyst   Inspector
    └─────┼─────────────┘
          ▼
    EvidenceAggregator
          │
         END   (interim — judges added in Phase 2)
    """
    builder = StateGraph(AgentState)

    # --- Add Nodes ---
    builder.add_node("ContextBuilder", context_builder_node)
    builder.add_node("ErrorHandler", error_handler_node)
    builder.add_node("RepoInvestigator", repo_investigator_node)
    builder.add_node("DocAnalyst", doc_analyst_node)
    builder.add_node("VisionInspector", vision_inspector_node)
    builder.add_node("EvidenceAggregator", evidence_aggregator_node)

    # --- Wire Edges ---
    # START → ContextBuilder
    builder.add_edge(START, "ContextBuilder")

    # ContextBuilder → conditional: invalid URL → ErrorHandler, valid → Fan-Out
    builder.add_conditional_edges(
        "ContextBuilder",
        route_after_context,
        {
            "error": "ErrorHandler",
            "ok": "RepoInvestigator",   # LangGraph fan-out: first parallel branch
        },
    )
    # Additional fan-out edges from ContextBuilder for parallel detectives
    # (LangGraph executes multiple add_edge targets from a conditional node in parallel)
    builder.add_edge("ContextBuilder", "DocAnalyst")
    builder.add_edge("ContextBuilder", "VisionInspector")

    # ErrorHandler → END (graceful failure)
    builder.add_edge("ErrorHandler", END)

    # All 3 Detectives → EvidenceAggregator [Fan-In]
    builder.add_edge("RepoInvestigator", "EvidenceAggregator")
    builder.add_edge("DocAnalyst", "EvidenceAggregator")
    builder.add_edge("VisionInspector", "EvidenceAggregator")

    # EvidenceAggregator → END (interim submission)
    builder.add_edge("EvidenceAggregator", END)

    # Compile the graph
    graph = builder.compile()
    logger.info("[GraphBuilder] Graph compiled successfully.")
    return graph


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def run_detective_audit(repo_url: str, pdf_path: str = "") -> Dict[str, Any]:
    """
    Run the Automaton Auditor detective graph against a target repo.

    Args:
        repo_url: GitHub repository URL to audit
        pdf_path: Optional path to PDF architectural report

    Returns:
        Final AgentState with all collected evidence
    """
    graph = build_graph()

    initial_state: AgentState = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "errors": [],
        "final_report": None,
    }

    logger.info(f"Starting audit of: {repo_url}")
    result = graph.invoke(initial_state)
    logger.info("Audit complete.")
    return result


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python -m src.graph <repo_url> [pdf_path]")
        print("Example: python -m src.graph https://github.com/user/repo reports/interim_report.pdf")
        sys.exit(1)

    repo_url = sys.argv[1]
    pdf_path = sys.argv[2] if len(sys.argv) > 2 else ""

    result = run_detective_audit(repo_url, pdf_path)

    # Print evidence summary
    print("\n" + "="*60)
    print("FINAL EVIDENCE SUMMARY")
    print("="*60)
    evidences = result.get("evidences", {})
    for detective, evs in evidences.items():
        print(f"\n[{detective.upper()} DETECTIVE — {len(evs)} items]")
        for ev in evs:
            status = "✓ FOUND" if ev.found else "✗ NOT FOUND"
            print(f"  {status} | {ev.goal} | confidence={ev.confidence:.2f}")
            print(f"    Location: {ev.location}")
            print(f"    Rationale: {ev.rationale[:150]}...")

    errors = result.get("errors", [])
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for err in errors:
            print(f"  ✗ {err}")
