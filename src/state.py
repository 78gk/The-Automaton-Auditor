"""
Automaton Auditor — Typed State Definitions
Uses Pydantic BaseModel + TypedDict with Annotated reducers
to support safe parallel agent execution without data overwrites.
"""

import operator
from typing import Annotated, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Layer 1: Detective Output — Forensic Evidence (objective facts only)
# ---------------------------------------------------------------------------

class Evidence(BaseModel):
    """Structured, bias-free evidence collected by a Detective agent."""

    goal: str = Field(description="The forensic goal this evidence addresses")
    found: bool = Field(description="Whether the artifact/pattern was found")
    content: Optional[str] = Field(
        default=None,
        description="Relevant code snippet, text excerpt, or log output",
    )
    location: str = Field(
        description="File path, line number, or commit hash where evidence was found"
    )
    rationale: str = Field(
        description="Rationale explaining confidence level and why this evidence supports the finding"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 (uncertain) and 1.0 (certain)",
    )


# ---------------------------------------------------------------------------
# Layer 2: Judicial Output — Opinions from distinct Judge personas
# ---------------------------------------------------------------------------

class JudicialOpinion(BaseModel):
    """A structured opinion from one of the three Judge personas."""

    judge: Literal["Prosecutor", "Defense", "TechLead"] = Field(
        description="Which judge persona produced this opinion"
    )
    criterion_id: str = Field(
        description="The rubric dimension ID this opinion addresses"
    )
    score: int = Field(
        ge=1,
        le=5,
        description="Score from 1 (worst) to 5 (best) for this criterion",
    )
    argument: str = Field(
        description="Detailed argument supporting the score, citing specific evidence"
    )
    cited_evidence: List[str] = Field(
        description="List of evidence goal IDs or locations cited in this argument"
    )


# ---------------------------------------------------------------------------
# Layer 3: Chief Justice Output — Final Verdict per Criterion
# ---------------------------------------------------------------------------

class CriterionResult(BaseModel):
    """The Chief Justice's final ruling on a single rubric criterion."""

    dimension_id: str = Field(description="Rubric dimension ID")
    dimension_name: str = Field(description="Human-readable dimension name")
    final_score: int = Field(
        ge=1,
        le=5,
        description="Deterministic final score after conflict resolution",
    )
    judge_opinions: List[JudicialOpinion] = Field(
        description="All three judge opinions for this criterion"
    )
    dissent_summary: Optional[str] = Field(
        default=None,
        description="Required when score variance across judges exceeds 2. Explains the conflict.",
    )
    remediation: str = Field(
        description="Specific, file-level instructions for improvement"
    )


class AuditReport(BaseModel):
    """The complete, production-grade audit report produced by the Chief Justice."""

    repo_url: str = Field(description="The GitHub repository URL that was audited")
    pdf_path: str = Field(description="Path to the PDF report that was analyzed")
    executive_summary: str = Field(
        description="High-level verdict: overall quality, key strengths, critical gaps"
    )
    overall_score: float = Field(
        ge=1.0,
        le=5.0,
        description="Aggregate score across all rubric dimensions",
    )
    criteria: List[CriterionResult] = Field(
        description="Detailed results for each rubric dimension"
    )
    remediation_plan: str = Field(
        description="Consolidated, prioritized remediation plan with file-level instructions"
    )


# ---------------------------------------------------------------------------
# Graph State — Shared mutable state for the entire LangGraph swarm
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """
    The single shared state object passed between all nodes in the StateGraph.

    Reducers:
    - evidences: operator.ior (dict merge) — allows parallel Detectives to each
      add their own key without overwriting others' data.
    - opinions: operator.add (list extend) — allows parallel Judges to each
      append their opinion without overwriting others' data.
    """

    repo_url: str
    pdf_path: str
    rubric_dimensions: List[Dict]

    # Parallel-safe: each Detective writes to its own key (e.g., "repo", "doc", "vision")
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]

    # Parallel-safe: each Judge appends its opinions to the shared list
    opinions: Annotated[List[JudicialOpinion], operator.add]

    # Written once by ChiefJustice at the end
    final_report: Optional[AuditReport]

    # Error tracking
    errors: Annotated[List[str], operator.add]
