# 🏛️ Automaton Auditor — The Digital Courtroom

A **hierarchical multi-agent LangGraph swarm** that performs forensic quality assurance on AI-generated codebases. Built for FDE Challenge Week 2.

## Architecture

The Digital Courtroom implements **two distinct parallel fan-out/fan-in patterns** — one for detectives and one for judges — connected by a synchronisation node:

```
START
  │
  ▼
ContextBuilder  ──[invalid URL]──►  ErrorHandler  ──► END
  │ [valid]
  │   ◄─── FAN-OUT 1: Detectives run in parallel ───►
  ├───────────────────┬───────────────────┐
  ▼                   ▼                   ▼
RepoInvestigator   DocAnalyst       VisionInspector
(AST + Git)      (PDF + RAG)       (Diagram Vision)
  │                   │                   │
  └───────────────────┴───────────────────┘
                       │   ◄─── FAN-IN 1 ───►
                       ▼
              EvidenceAggregator
              (cross-reference + hallucination check)
                       │
                       │   ◄─── FAN-OUT 2: Judges run in parallel ───►
                       ├───────────────────┬───────────────────┐
                       ▼                   ▼                   ▼
                  Prosecutor           Defense             TechLead
                 (adversarial)        (forgiving)         (pragmatic)
                 score + args        score + args        score + args
                       │                   │                   │
                       └───────────────────┴───────────────────┘
                                           │   ◄─── FAN-IN 2 ───►
                                           ▼
                                     ChiefJustice
                              (deterministic synthesis)
                              Security Override · Fact Supremacy
                              TechLead Weight · Variance Rule
                                           │
                                           ▼
                                  Markdown Audit Report
                                    (audit/audit_report.md)
```

![StateGraph Architecture](reports/stategraph_architecture.png)

### Graph wiring (from `src/graph.py`)

```python
# Fan-Out 1: Detectives in parallel
builder.add_conditional_edges("ContextBuilder", route_after_context)
# route_after_context() returns ["RepoInvestigator", "DocAnalyst", "VisionInspector"]

# Fan-In 1: All detectives → EvidenceAggregator
builder.add_edge("RepoInvestigator", "EvidenceAggregator")
builder.add_edge("DocAnalyst", "EvidenceAggregator")
builder.add_edge("VisionInspector", "EvidenceAggregator")

# Fan-Out 2: Judges in parallel
builder.add_edge("EvidenceAggregator", "Prosecutor")
builder.add_edge("EvidenceAggregator", "Defense")
builder.add_edge("EvidenceAggregator", "TechLead")

# Fan-In 2: All judges → ChiefJustice
builder.add_edge("Prosecutor", "ChiefJustice")
builder.add_edge("Defense", "ChiefJustice")
builder.add_edge("TechLead", "ChiefJustice")

builder.add_edge("ChiefJustice", END)
```

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- `git` installed and on PATH

### Install

```bash
# Clone this repo
git clone <this-repo-url>
cd automaton-auditor

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

Required keys (at least one LLM key):

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | Google Gemini API key (preferred) |
| `OPENAI_API_KEY` | OpenAI API key (fallback) |
| `LANGCHAIN_API_KEY` | LangSmith API key for tracing |
| `LANGCHAIN_TRACING_V2` | Set to `true` to enable tracing |
| `LANGCHAIN_PROJECT` | LangSmith project name |

## Usage

### Run the Full Audit (Detectives + Judges + ChiefJustice)

```bash
# Against any public GitHub repo (with PDF report)
python -m src.graph https://github.com/owner/repo-name path/to/report.pdf

# Output goes to audit/audit_report.md by default
# Specify a custom output directory:
python -m src.graph https://github.com/owner/repo-name path/to/report.pdf audit/report_onpeer_generated
```

### Run as a module

```python
from src.graph import run_audit

result = run_audit(
    repo_url="https://github.com/owner/repo",
    pdf_path="reports/final_report.pdf",
    output_dir="audit/report_onself_generated"
)

# Access evidence
for detective, evidences in result["evidences"].items():
    for ev in evidences:
        print(f"[{detective}] {ev.goal}: found={ev.found}, confidence={ev.confidence}")

# Access judicial opinions
for opinion in result["opinions"]:
    print(f"[{opinion.judge}] {opinion.criterion_id}: {opinion.score}/5")

# Access final report
report = result["final_report"]
print(f"Overall Score: {report.overall_score}/5")
```

## Project Structure

```
automaton-auditor/
├── src/
│   ├── __init__.py
│   ├── state.py              # Pydantic models + TypedDict AgentState
│   ├── graph.py              # LangGraph StateGraph (fan-out/fan-in)
│   ├── nodes/
│   │   ├── detectives.py     # RepoInvestigator, DocAnalyst, VisionInspector
│   │   ├── judges.py         # Prosecutor, Defense, TechLead (Phase 2)
│   │   └── justice.py        # ChiefJustice synthesis engine (Phase 2)
│   └── tools/
│       ├── repo_tools.py     # Git clone (sandboxed), AST parser
│       └── doc_tools.py      # PDF ingestion (docling), cross-reference
├── reports/
│   ├── final_report.pdf           # Final architectural report (Saturday submission)
│   ├── interim_report.pdf         # Interim architectural report (Wednesday submission)
│   └── stategraph_architecture.png  # StateGraph architecture diagram
├── audit/
│   ├── report_onself_generated/   # Self-audit report (agent on own repo)
│   ├── report_onpeer_generated/   # Peer-audit report (agent on peer's repo)
│   └── report_bypeer_received/    # Peer's report on your repo
├── rubric.json               # Machine-readable rubric (the Constitution)
├── pyproject.toml            # uv-managed dependencies
├── .env.example              # Environment variable template
└── README.md
```

## Key Design Decisions

### Why Pydantic over plain dicts?
Strict typing enforces schema contracts between agents. A `JudicialOpinion` object with `score: int = Field(ge=1, le=5)` **cannot** receive a score of 6 — the model validates at construction time, not at runtime when it's too late.

### Why AST parsing over regex?
Regex matches text; AST matches **structure**. A regex for `StateGraph` would match a comment `# StateGraph not used`. AST parsing verifies that `StateGraph(AgentState)` is actually instantiated and used.

### Why `operator.ior` and `operator.add`?
When 3 agents run in parallel and write to the same state, LangGraph needs to know how to **merge** their outputs. `operator.ior` (dict union) lets each Detective write to its own key without overwriting others. `operator.add` (list extend) lets each Judge append without overwriting.

### Why tempfile for git clone?
Security isolation. Cloning unknown repos into the live working directory risks: path traversal attacks, overwriting source files, and leaving artifacts on disk. `tempfile.TemporaryDirectory()` creates an auto-cleaned sandbox.

## Rubric

The `rubric.json` file is the agent's **Constitution** — 10 forensic dimensions loaded at runtime:

1. Git Forensic Analysis
2. State Management Rigor
3. Graph Orchestration Architecture
4. Safe Tool Engineering
5. Structured Output Enforcement
6. Judicial Nuance and Dialectics
7. Chief Justice Synthesis Engine
8. Theoretical Depth (Documentation)
9. Report Accuracy (Cross-Reference)
10. Architectural Diagram Analysis

## LangSmith Trace

The complete end-to-end execution of the Automaton Auditor is traced in LangSmith for full observability:

**🔗 Trace URL:** https://smith.langchain.com/public/8b41fac0-6194-4631-81fa-a2d1d1cdcd08/r

**Project:** `automaton-auditor`

The trace demonstrates:
- ✅ Complete pipeline execution from START to END
- ✅ All three detective agents running in parallel (fan-out)
- ✅ Evidence aggregation (fan-in #1)
- ✅ All three judge agents running in parallel (fan-out)
- ✅ Chief Justice synthesis with deterministic conflict resolution (fan-in #2)
- ✅ Structured outputs at each layer (Evidence → JudicialOpinion → AuditReport)
- ✅ No terminal failures or unhandled errors

## Status

| Layer | Status |
|---|---|
| Infrastructure (state, tools) | ✅ Complete |
| Detective Layer (RepoInvestigator, DocAnalyst, VisionInspector) | ✅ Complete |
| EvidenceAggregator (Fan-In) | ✅ Complete |
| Judicial Layer (Prosecutor, Defense, TechLead) | ✅ Complete — wired with `.with_structured_output(JudicialOpinion)` |
| Chief Justice Synthesis | ✅ Complete — deterministic rules (Security Override, Fact Supremacy, Variance Rule) |
| Full End-to-End Report | ✅ Complete — Markdown serialization to `audit/audit_report.md` |
| LangSmith Tracing | ✅ Enabled — See trace URL above |
