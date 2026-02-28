"""
Automaton Auditor — Chief Justice Synthesis Engine
Implements deterministic conflict resolution (NOT LLM averaging).

Rules (hardcoded Python logic):
1. Rule of Security: confirmed security flaw → score capped at 3
2. Rule of Evidence (Fact Supremacy): detective facts override judicial opinions
3. Rule of Functionality: Tech Lead weight highest for architecture criteria
4. Variance Rule: score variance > 2 → requires dissent summary
5. Variance Re-evaluation: variance > 2 → re-evaluate before final score
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.state import AgentState, AuditReport, CriterionResult, Evidence, JudicialOpinion

logger = logging.getLogger(__name__)

# Criteria where Tech Lead opinion carries highest weight
ARCHITECTURE_CRITERIA = {
    "graph_orchestration",
    "state_management_rigor",
    "safe_tool_engineering",
    "structured_output_enforcement",
}

# Criteria where Detective evidence is strictly required
FACT_DEPENDENT_CRITERIA = {
    "git_forensic_analysis",
    "state_management_rigor",
    "graph_orchestration",
    "safe_tool_engineering",
    "structured_output_enforcement",
    "chief_justice_synthesis",
}


# ---------------------------------------------------------------------------
# Conflict Resolution Logic (Deterministic)
# ---------------------------------------------------------------------------

def check_security_violation(evidences: Dict[str, List[Evidence]]) -> bool:
    """
    Rule of Security: Check if any Detective found a confirmed security violation.

    Uses structured evidence fields — NOT string matching on free-text content.
    A violation is confirmed when:
      - The detective goal is 'safe_tool_engineering'
      - found=False (the safety requirement was NOT met)
      - confidence >= 0.7 (high-confidence finding, not a guess)

    This ensures only forensically verified violations trigger the override,
    not incidental mentions of 'os.system' in comments or documentation.
    """
    for detective, ev_list in evidences.items():
        for ev in ev_list:
            if (
                ev.goal == "safe_tool_engineering"
                and not ev.found
                and ev.confidence >= 0.7
            ):
                # Check rationale for explicit security violation indicators
                # (structured keywords only — not free-form content scanning)
                violation_keywords = [
                    "os.system", "shell injection", "no sandboxing",
                    "no tempfile", "unsanitized", "security violation",
                    "security negligence",
                ]
                rationale_lower = (ev.rationale or "").lower()
                if any(kw in rationale_lower for kw in violation_keywords):
                    logger.warning(
                        f"[ChiefJustice] Security violation confirmed by "
                        f"{detective} detective: {ev.rationale[:200]}"
                    )
                    return True
    return False


def check_artifact_missing(
    criterion_id: str,
    evidences: Dict[str, List[Evidence]],
) -> bool:
    """
    Rule of Evidence: Check if Detective evidence shows an artifact is missing
    for a given criterion. Used to override Defense hallucinations.
    """
    for detective, ev_list in evidences.items():
        for ev in ev_list:
            if ev.goal == criterion_id and not ev.found and ev.confidence > 0.7:
                return True
    return False


def resolve_scores(
    criterion_id: str,
    opinions: List[JudicialOpinion],
    evidences: Dict[str, List[Evidence]],
    has_security_violation: bool,
) -> Tuple[int, Optional[str]]:
    """
    Deterministic score resolution for a single criterion.
    Returns (final_score, dissent_summary_or_None).
    """
    if not opinions:
        return 1, "No judicial opinions provided — insufficient evidence for scoring."

    scores = {op.judge: op.score for op in opinions}
    prosecutor_score = scores.get("Prosecutor", 3)
    defense_score = scores.get("Defense", 3)
    tech_lead_score = scores.get("TechLead", 3)

    all_scores = list(scores.values())
    variance = max(all_scores) - min(all_scores)

    # --- Rule of Security ---
    if has_security_violation and criterion_id in ("safe_tool_engineering", "graph_orchestration"):
        final_score = min(3, max(all_scores))  # Cap at 3
        dissent = (
            f"SECURITY OVERRIDE APPLIED: A confirmed security violation was detected. "
            f"Score capped at 3 regardless of Defense arguments. "
            f"Prosecutor={prosecutor_score}, Defense={defense_score}, TechLead={tech_lead_score}."
        ) if variance > 0 else None
        return final_score, dissent

    # --- Rule of Evidence (Fact Supremacy) ---
    if criterion_id in FACT_DEPENDENT_CRITERIA:
        artifact_missing = check_artifact_missing(criterion_id, evidences)
        if artifact_missing and defense_score > 3:
            # Defense is overruled — artifact doesn't exist
            adjusted_defense = min(defense_score, 2)
            all_scores_adjusted = [
                s if judge != "Defense" else adjusted_defense
                for judge, s in scores.items()
            ]
            fact_note = (
                f"FACT SUPREMACY APPLIED: Detective evidence confirms artifact for "
                f"'{criterion_id}' is missing or not found (confidence > 70%). "
                f"Defense score adjusted from {defense_score} to {adjusted_defense}."
            )
            all_scores = all_scores_adjusted
            defense_score = adjusted_defense
        else:
            fact_note = None
    else:
        fact_note = None

    # --- Rule of Functionality (Tech Lead Weight) ---
    if criterion_id in ARCHITECTURE_CRITERIA:
        # Tech Lead carries highest weight (2x)
        weighted_scores = [prosecutor_score, defense_score, tech_lead_score, tech_lead_score]
        final_score = round(sum(weighted_scores) / len(weighted_scores))
    else:
        # Equal weighting
        final_score = round(sum(all_scores) / len(all_scores))

    # Clamp to valid range
    final_score = max(1, min(5, final_score))

    # --- Variance Rule: Require dissent summary if variance > 2 ---
    dissent_summary = None
    if variance > 2:
        prosecutor_arg = next((op.argument for op in opinions if op.judge == "Prosecutor"), "N/A")
        defense_arg = next((op.argument for op in opinions if op.judge == "Defense"), "N/A")
        tech_lead_arg = next((op.argument for op in opinions if op.judge == "TechLead"), "N/A")

        dissent_summary = (
            f"DISSENT (variance={variance}): "
            f"Prosecutor ({prosecutor_score}): {prosecutor_arg[:200]}... | "
            f"Defense ({defense_score}): {defense_arg[:200]}... | "
            f"TechLead ({tech_lead_score}): {tech_lead_arg[:200]}..."
        )
        if fact_note:
            dissent_summary = fact_note + " | " + dissent_summary

    return final_score, dissent_summary


def build_remediation(criterion_id: str, final_score: int, opinions: List[JudicialOpinion]) -> str:
    """Build specific, file-level remediation instructions based on the verdict."""
    REMEDIATION_TEMPLATES = {
        "git_forensic_analysis": {
            1: "Create meaningful atomic commits. Run: git log --oneline to verify progression. Each commit should represent one logical step (setup → tools → graph).",
            3: "Add more descriptive commit messages referencing specific files changed. Ensure >3 commits with clear progression.",
            5: "Git history is exemplary. No remediation needed.",
        },
        "state_management_rigor": {
            1: "Replace all plain dicts with Pydantic BaseModel classes. Add operator.add and operator.ior reducers to AgentState fields in src/state.py.",
            3: "Verify Annotated[List[JudicialOpinion], operator.add] and Annotated[Dict[str, List[Evidence]], operator.ior] are in AgentState.",
            5: "State management is rigorous. No remediation needed.",
        },
        "graph_orchestration": {
            1: "Refactor src/graph.py to use parallel fan-out. Add edges from ContextBuilder to all 3 Detectives simultaneously. Add EvidenceAggregator as fan-in.",
            3: "Add conditional edges for error handling. Verify Judges also run in parallel fan-out from EvidenceAggregator.",
            5: "Graph orchestration is exemplary. No remediation needed.",
        },
        "safe_tool_engineering": {
            1: "CRITICAL: Replace os.system() with subprocess.run(). Wrap all git operations in tempfile.TemporaryDirectory() in src/tools/repo_tools.py.",
            3: "Add try/except around subprocess.run() calls. Validate repo URL before cloning. Handle authentication errors.",
            5: "Tool engineering is secure. No remediation needed.",
        },
        "structured_output_enforcement": {
            1: "In src/nodes/judges.py, use llm.with_structured_output(JudicialOpinion) for all three judge LLM calls.",
            3: "Add retry logic for malformed outputs. Validate output against JudicialOpinion schema before appending to state.",
            5: "Structured output enforcement is complete. No remediation needed.",
        },
        "judicial_nuance": {
            1: "Implement three distinct judge personas in src/nodes/judges.py. Prosecutor must be adversarial; Defense must be forgiving; TechLead must be pragmatic.",
            3: "Increase persona differentiation. Ensure Prosecutor and Defense produce scores that differ by at least 1-2 points on most criteria.",
            5: "Dialectical synthesis is functioning. No remediation needed.",
        },
        "chief_justice_synthesis": {
            1: "Implement deterministic Python rules in src/nodes/justice.py. Do NOT use LLM averaging. Add security_override, fact_supremacy, and variance rules.",
            3: "Add dissent_summary generation for criteria with variance > 2. Ensure output is a Markdown file, not console text.",
            5: "Chief Justice synthesis is complete. No remediation needed.",
        },
    }

    templates = REMEDIATION_TEMPLATES.get(criterion_id, {})
    # Find closest score bucket
    for score_threshold in [1, 3, 5]:
        if final_score <= score_threshold:
            return templates.get(score_threshold, f"Review and improve {criterion_id} implementation.")

    # Extract from judge opinions as fallback
    tech_lead_opinion = next((op for op in opinions if op.judge == "TechLead"), None)
    if tech_lead_opinion:
        return f"Tech Lead recommendation: {tech_lead_opinion.argument[:300]}"

    return f"Review {criterion_id} implementation against rubric success patterns."


# ---------------------------------------------------------------------------
# Chief Justice Node
# ---------------------------------------------------------------------------

def chief_justice_node(state: AgentState) -> Dict:
    """
    The Supreme Court. Synthesizes all judicial opinions into a final verdict.
    Uses deterministic Python logic — NOT LLM averaging.
    """
    evidences = state.get("evidences", {})
    opinions = state.get("opinions", [])
    rubric_dims = state.get("rubric_dimensions", [])
    repo_url = state.get("repo_url", "")
    pdf_path = state.get("pdf_path", "")

    logger.info(f"[ChiefJustice] Synthesizing {len(opinions)} opinions across {len(rubric_dims)} dimensions.")

    # Check global security violation (affects multiple criteria)
    has_security_violation = check_security_violation(evidences)
    if has_security_violation:
        logger.warning("[ChiefJustice] SECURITY VIOLATION detected — applying security override.")

    # Group opinions by criterion
    opinions_by_criterion: Dict[str, List[JudicialOpinion]] = {}
    for op in opinions:
        opinions_by_criterion.setdefault(op.criterion_id, []).append(op)

    # Build CriterionResult for each rubric dimension
    criteria_results: List[CriterionResult] = []
    total_score = 0.0

    for dim in rubric_dims:
        dim_id = dim["id"]
        dim_name = dim["name"]
        dim_opinions = opinions_by_criterion.get(dim_id, [])

        final_score, dissent_summary = resolve_scores(
            dim_id, dim_opinions, evidences, has_security_violation
        )

        remediation = build_remediation(dim_id, final_score, dim_opinions)

        criteria_results.append(CriterionResult(
            dimension_id=dim_id,
            dimension_name=dim_name,
            final_score=final_score,
            judge_opinions=dim_opinions,
            dissent_summary=dissent_summary,
            remediation=remediation,
        ))
        total_score += final_score
        logger.info(f"[ChiefJustice] {dim_id}: final_score={final_score}")

    overall_score = round(total_score / len(criteria_results), 2) if criteria_results else 0.0

    # Build executive summary
    executive_summary = _build_executive_summary(
        overall_score, criteria_results, has_security_violation
    )

    # Build consolidated remediation plan
    remediation_plan = _build_remediation_plan(criteria_results)

    report = AuditReport(
        repo_url=repo_url,
        pdf_path=pdf_path,
        executive_summary=executive_summary,
        overall_score=overall_score,
        criteria=criteria_results,
        remediation_plan=remediation_plan,
    )

    # Serialize to Markdown — write to the output_dir passed via state
    # Default to "audit" if not specified
    output_dir = state.get("output_dir", "audit")
    markdown_path = _serialize_to_markdown(report, output_dir=output_dir)
    logger.info(f"[ChiefJustice] Audit report written to: {markdown_path}")

    return {"final_report": report}


def _build_executive_summary(
    overall_score: float,
    criteria: List[CriterionResult],
    has_security_violation: bool,
) -> str:
    score_label = (
        "Master Thinker (5/5)" if overall_score >= 4.5 else
        "Competent Orchestrator (3-4/5)" if overall_score >= 3.0 else
        "Vibe Coder (1-2/5)"
    )
    low_scores = [c for c in criteria if c.final_score <= 2]
    high_scores = [c for c in criteria if c.final_score >= 4]

    summary = f"**Overall Score: {overall_score:.1f}/5 — {score_label}**\n\n"
    if has_security_violation:
        summary += "⚠️ **SECURITY VIOLATION DETECTED** — Security override applied to affected criteria.\n\n"
    if high_scores:
        summary += f"**Strengths:** {', '.join(c.dimension_name for c in high_scores)}\n\n"
    if low_scores:
        summary += f"**Critical Gaps:** {', '.join(c.dimension_name for c in low_scores)}\n\n"
    return summary.strip()


def _build_remediation_plan(criteria: List[CriterionResult]) -> str:
    lines = ["# Consolidated Remediation Plan\n"]
    # Sort by score ascending (most critical first)
    sorted_criteria = sorted(criteria, key=lambda c: c.final_score)
    for c in sorted_criteria:
        priority = "🔴 CRITICAL" if c.final_score <= 2 else "🟡 MODERATE" if c.final_score <= 3 else "🟢 MINOR"
        lines.append(f"## {priority} — {c.dimension_name} (Score: {c.final_score}/5)")
        lines.append(c.remediation)
        lines.append("")
    return "\n".join(lines)


def _serialize_to_markdown(report: AuditReport, output_dir: str = "audit") -> str:
    """Serialize AuditReport to a production-grade Markdown file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = output_path / "audit_report.md"
    lines = [
        "# 🏛️ Automaton Auditor — Audit Report",
        f"**Repository:** {report.repo_url}",
        f"**PDF Report:** {report.pdf_path}",
        f"**Overall Score:** {report.overall_score:.1f} / 5.0",
        "",
        "---",
        "",
        "## Executive Summary",
        report.executive_summary,
        "",
        "---",
        "",
        "## Criterion Breakdown",
        "",
    ]

    for criterion in report.criteria:
        lines.append(f"### {criterion.dimension_name}")
        lines.append(f"**Final Score:** {criterion.final_score}/5")
        lines.append("")

        # Judge opinions
        for opinion in criterion.judge_opinions:
            icon = {"Prosecutor": "⚖️", "Defense": "🛡️", "TechLead": "🔧"}.get(opinion.judge, "👤")
            lines.append(f"#### {icon} {opinion.judge} (Score: {opinion.score}/5)")
            lines.append(opinion.argument)
            if opinion.cited_evidence:
                lines.append(f"*Cited evidence:* {', '.join(opinion.cited_evidence)}")
            lines.append("")

        # Dissent summary (required when variance > 2)
        if criterion.dissent_summary:
            lines.append(f"> **⚡ DISSENT:** {criterion.dissent_summary}")
            lines.append("")

        # Remediation
        lines.append(f"**📋 Remediation:** {criterion.remediation}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Consolidated remediation plan
    lines.append(report.remediation_plan)

    markdown_content = "\n".join(lines)
    filename.write_text(markdown_content, encoding="utf-8")
    return str(filename)
