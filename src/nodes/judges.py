"""
Automaton Auditor — Judicial Layer Nodes (FULLY IMPLEMENTED)
Implements Prosecutor, Defense, and TechLead as parallel LangGraph nodes.
Each judge receives the same evidence and produces a distinct JudicialOpinion
using .with_structured_output(JudicialOpinion) for strict schema enforcement.

All three judge nodes are LIVE and wired into src/graph.py:
  EvidenceAggregator → [Prosecutor ‖ Defense ‖ TechLead] → ChiefJustice

Architecture:
- Prosecutor (temp=0.1): adversarial, finds gaps/security flaws/laziness
- Defense    (temp=0.3): optimistic, rewards effort/intent/creativity
- TechLead   (temp=0.1): pragmatic, evaluates architectural soundness

All use .with_structured_output(JudicialOpinion) — freeform text is REJECTED.
"""

import logging
import os
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from src.state import AgentState, Evidence, JudicialOpinion

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM Factory with Structured Output
# ---------------------------------------------------------------------------

def get_judge_llm(temperature: float = 0.3):
    """
    Return LLM configured for structured judicial output.
    Priority: Groq (free, generous quota) → Google Gemini → OpenAI
    """
    groq_key = os.getenv("GROQ_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if groq_key:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=temperature,
                groq_api_key=groq_key,
            )
        except ImportError:
            logger.warning("[LLM] langchain-groq not installed, falling back.")

    if google_key:
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=temperature,
            google_api_key=google_key,
        )
    elif openai_key:
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            api_key=openai_key,
        )
    else:
        raise ValueError(
            "No LLM API key found. Set GROQ_API_KEY, GOOGLE_API_KEY, or OPENAI_API_KEY in .env"
        )


# ---------------------------------------------------------------------------
# Judge System Prompts (Distinct Personas — Anti-Collusion)
# ---------------------------------------------------------------------------

PROSECUTOR_SYSTEM_PROMPT = """You are THE PROSECUTOR in a Digital Courtroom auditing an AI codebase.

CORE PHILOSOPHY: "Trust No One. Assume Vibe Coding."
YOUR MISSION: Find gaps, security flaws, architectural laziness, and shortcuts.

STRICT RULES:
- If parallelism is claimed but the graph is linear → charge "Orchestration Fraud" → Score: 1
- If judges return freeform text instead of Pydantic models → charge "Hallucination Liability" → Score: 2 max
- If os.system() is used for git operations → charge "Security Negligence" → Score: 1
- If state uses plain dicts instead of Pydantic → charge "Technical Debt" → Score: 2 max
- If commit history is a single "init" dump → charge "Process Fraud" → Score: 1

CRITERION PRIORITIES (what you focus hardest on):
- safe_tool_engineering: os.system(), unsanitized URLs, missing error handling
- git_forensic_analysis: bulk uploads, missing progression, unclear commit messages
- graph_orchestration: linear flow masquerading as parallel, missing fan-in
- state_management_rigor: plain dicts, missing reducers, no Pydantic validation
- structured_output_enforcement: freeform LLM responses, no schema binding

You MUST:
- Be adversarial and skeptical. Assume the worst.
- Cite SPECIFIC evidence (file paths, line content, commit hashes).
- Provide a HARSH score (1-3 range typical).
- List every missing element explicitly.
- Never give benefit of the doubt without concrete proof.
- ONLY reference evidence items listed in the Forensic Evidence Summary. Do not invent evidence.

You are NOT here to be fair. You are here to find what's broken."""

DEFENSE_SYSTEM_PROMPT = """You are THE DEFENSE ATTORNEY in a Digital Courtroom auditing an AI codebase.

CORE PHILOSOPHY: "Reward Effort and Intent. Look for the Spirit of the Law."
YOUR MISSION: Highlight creative workarounds, deep thought, and effort — even in imperfect implementations.

MITIGATION STRATEGIES:
- If the graph fails to compile but the AST parsing logic is sophisticated → argue "Deep Code Comprehension" → Boost from 1 to 3
- If ChiefJustice uses LLM instead of hardcoded rules but judge personas are highly distinct → argue "Role Separation Success" → Score 3-4
- If commit history shows struggle and iteration → argue "Engineering Process" → Higher score based on effort
- If state uses TypedDict instead of full Pydantic but reducers are correct → argue "Pragmatic Architecture" → Score 3

CRITERION PRIORITIES (what you defend hardest on):
- theoretical_depth: even partial explanations of complex concepts deserve credit
- judicial_nuance: distinct personas with different philosophies = strong dialectical intent
- chief_justice_synthesis: any deterministic logic (even partial) beats pure LLM averaging
- report_accuracy: minor path discrepancies do not negate overall report quality

You MUST:
- Be optimistic and generous. Look for what WORKS, not what's broken.
- Cite the SPIRIT of requirements, not just the letter.
- Provide a GENEROUS score (3-5 range typical).
- Find at least one genuine strength in every criterion.
- Argue for partial credit wherever effort is demonstrated.
- CRITICAL: You may ONLY cite evidence items listed in the Forensic Evidence Summary. 
  Do NOT fabricate or assume the existence of artifacts not listed there.
  If an artifact is absent, argue for effort and intent — but acknowledge the absence.

You are NOT here to be strict. You are here to find what's working."""

TECH_LEAD_SYSTEM_PROMPT = """You are THE TECH LEAD in a Digital Courtroom auditing an AI codebase.

CORE PHILOSOPHY: "Does it actually work? Is it maintainable? Will it scale?"
YOUR MISSION: Evaluate architectural soundness, code cleanliness, and practical production viability.

TECHNICAL PRECEDENTS:
- "Pydantic Rigor": State using plain dicts = "Technical Debt" → Score: 3 (works but brittle)
- "Sandboxed Tooling": os.system for git = "Security Negligence" → Overrides all effort points
- "Parallel Architecture": Linear graph = fundamental bottleneck → Score: 1-2
- "Structured Output": No .with_structured_output() = unreliable pipeline → Score: 2

You ARE the tie-breaker between Prosecutor and Defense:
- If Prosecutor says 1 (security flaw) and Defense says 5 (great effort) → assess actual technical debt → give 1, 2, or 3
- If code is imperfect but architecturally sound → give 3-4 with specific remediation advice
- Focus on: Does it compile? Does the state flow correctly? Are tools isolated?

You MUST:
- Ignore "vibes" and "struggle stories." Focus on artifacts.
- Provide a REALISTIC score (1, 2, 3, 4, or 5) with clear technical rationale.
- Give specific, file-level remediation advice.
- Be the pragmatic voice of reason between the extremes."""


# ---------------------------------------------------------------------------
# Evidence Formatter (shared across all judges)
# ---------------------------------------------------------------------------

def format_evidence_for_judges(evidences: Dict[str, List[Evidence]]) -> str:
    """Format all collected evidence into a structured context string for judges."""
    lines = ["# FORENSIC EVIDENCE SUMMARY\n"]
    for detective, ev_list in evidences.items():
        lines.append(f"## {detective.upper()} DETECTIVE FINDINGS\n")
        for ev in ev_list:
            status = "✓ FOUND" if ev.found else "✗ NOT FOUND"
            lines.append(f"### {ev.goal} [{status}]")
            lines.append(f"- **Location:** {ev.location}")
            lines.append(f"- **Confidence:** {ev.confidence:.0%}")
            lines.append(f"- **Rationale:** {ev.rationale}")
            if ev.content:
                lines.append(f"- **Content excerpt:**\n```\n{ev.content[:500]}\n```")
            lines.append("")
    return "\n".join(lines)


def build_judge_prompt(criterion_id: str, criterion_name: str, evidence_context: str, rubric_dimensions: list) -> str:
    """Build the human turn prompt for a judge evaluating a specific criterion."""
    # Find the relevant rubric dimension
    judicial_logic = next(
        (d for d in rubric_dimensions if d.get("id") == criterion_id),
        {}
    )
    success_pattern = judicial_logic.get("success_pattern", "Not specified")
    failure_pattern = judicial_logic.get("failure_pattern", "Not specified")

    return f"""## YOUR ASSIGNMENT
You must evaluate the criterion: **{criterion_name}** (ID: `{criterion_id}`)

## RUBRIC STANDARDS
- **Success Pattern (Score 5):** {success_pattern}
- **Failure Pattern (Score 1):** {failure_pattern}

## FORENSIC EVIDENCE
{evidence_context}

## INSTRUCTIONS
Based on your persona and the evidence above, render your verdict on the `{criterion_id}` criterion.
Provide: a score (1-5), a detailed argument citing specific evidence, and a list of evidence keys you cited.
Stay strictly in character. Do NOT break persona."""


# ---------------------------------------------------------------------------
# Judge Nodes (Parallel Execution)
# ---------------------------------------------------------------------------

def prosecutor_node(state: AgentState) -> Dict[str, Any]:
    """
    The Prosecutor Judge — adversarial, finds gaps and security flaws.
    Uses .with_structured_output(JudicialOpinion) for schema enforcement.
    """
    evidences = state.get("evidences", {})
    rubric_dims = state.get("rubric_dimensions", [])
    opinions: List[JudicialOpinion] = []
    errors: List[str] = []

    evidence_context = format_evidence_for_judges(evidences)
    repo_dims = [d for d in rubric_dims if d.get("target_artifact") == "github_repo"]

    try:
        llm = get_judge_llm(temperature=0.1)  # Lowest temp: most skeptical, least creative
        structured_llm = llm.with_structured_output(JudicialOpinion)

        for dim in repo_dims:
            try:
                prompt = build_judge_prompt(
                    dim["id"], dim["name"], evidence_context, rubric_dims
                )
                messages = [
                    SystemMessage(content=PROSECUTOR_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
                opinion: JudicialOpinion = structured_llm.invoke(messages)
                # Enforce judge field
                opinion = JudicialOpinion(
                    judge="Prosecutor",
                    criterion_id=dim["id"],
                    score=opinion.score,
                    argument=opinion.argument,
                    cited_evidence=opinion.cited_evidence,
                )
                opinions.append(opinion)
                logger.info(f"[Prosecutor] {dim['id']}: score={opinion.score}")
            except Exception as e:
                errors.append(f"Prosecutor failed on {dim['id']}: {e}")
                logger.error(f"[Prosecutor] Error on {dim['id']}: {e}")
    except Exception as e:
        errors.append(f"Prosecutor initialization failed: {e}")

    return {"opinions": opinions, "errors": errors}


def defense_node(state: AgentState) -> Dict[str, Any]:
    """
    The Defense Attorney Judge — optimistic, rewards effort and intent.
    Uses .with_structured_output(JudicialOpinion) for schema enforcement.
    """
    evidences = state.get("evidences", {})
    rubric_dims = state.get("rubric_dimensions", [])
    opinions: List[JudicialOpinion] = []
    errors: List[str] = []

    evidence_context = format_evidence_for_judges(evidences)
    repo_dims = [d for d in rubric_dims if d.get("target_artifact") == "github_repo"]

    try:
        llm = get_judge_llm(temperature=0.3)
        structured_llm = llm.with_structured_output(JudicialOpinion)

        for dim in repo_dims:
            try:
                prompt = build_judge_prompt(
                    dim["id"], dim["name"], evidence_context, rubric_dims
                )
                messages = [
                    SystemMessage(content=DEFENSE_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
                opinion: JudicialOpinion = structured_llm.invoke(messages)
                opinion = JudicialOpinion(
                    judge="Defense",
                    criterion_id=dim["id"],
                    score=opinion.score,
                    argument=opinion.argument,
                    cited_evidence=opinion.cited_evidence,
                )
                opinions.append(opinion)
                logger.info(f"[Defense] {dim['id']}: score={opinion.score}")
            except Exception as e:
                errors.append(f"Defense failed on {dim['id']}: {e}")
                logger.error(f"[Defense] Error on {dim['id']}: {e}")
    except Exception as e:
        errors.append(f"Defense initialization failed: {e}")

    return {"opinions": opinions, "errors": errors}


def tech_lead_node(state: AgentState) -> Dict[str, Any]:
    """
    The Tech Lead Judge — pragmatic, evaluates architectural soundness.
    Uses .with_structured_output(JudicialOpinion) for schema enforcement.
    """
    evidences = state.get("evidences", {})
    rubric_dims = state.get("rubric_dimensions", [])
    opinions: List[JudicialOpinion] = []
    errors: List[str] = []

    evidence_context = format_evidence_for_judges(evidences)
    repo_dims = [d for d in rubric_dims if d.get("target_artifact") == "github_repo"]

    try:
        llm = get_judge_llm(temperature=0.1)
        structured_llm = llm.with_structured_output(JudicialOpinion)

        for dim in repo_dims:
            try:
                prompt = build_judge_prompt(
                    dim["id"], dim["name"], evidence_context, rubric_dims
                )
                messages = [
                    SystemMessage(content=TECH_LEAD_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
                opinion: JudicialOpinion = structured_llm.invoke(messages)
                opinion = JudicialOpinion(
                    judge="TechLead",
                    criterion_id=dim["id"],
                    score=opinion.score,
                    argument=opinion.argument,
                    cited_evidence=opinion.cited_evidence,
                )
                opinions.append(opinion)
                logger.info(f"[TechLead] {dim['id']}: score={opinion.score}")
            except Exception as e:
                errors.append(f"TechLead failed on {dim['id']}: {e}")
                logger.error(f"[TechLead] Error on {dim['id']}: {e}")
    except Exception as e:
        errors.append(f"TechLead initialization failed: {e}")

    return {"opinions": opinions, "errors": errors}
