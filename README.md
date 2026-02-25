# 🏛️ Automaton Auditor — The Digital Courtroom

A **hierarchical multi-agent LangGraph swarm** that performs forensic quality assurance on AI-generated codebases. Built for FDE Challenge Week 2.

## Architecture

```
START
  │
  ▼
ContextBuilder (loads rubric)
  │
  ├──────────────────────────────┐──────────────────────────────┐
  ▼                              ▼                              ▼
RepoInvestigator           DocAnalyst                  VisionInspector
(AST + Git forensics)    (PDF ingestion + RAG)       (Diagram analysis)
  │                              │                              │
  └──────────────────────────────┴──────────────────────────────┘
                                 │
                                 ▼
                        EvidenceAggregator (Fan-In)
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
          Prosecutor          Defense            TechLead
         (adversarial)       (forgiving)        (pragmatic)
              │                  │                  │
              └──────────────────┴──────────────────┘
                                 │
                                 ▼
                           ChiefJustice
                    (deterministic synthesis)
                                 │
                                 ▼
                        Markdown Audit Report
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

### Run the Detective Audit (Interim — Evidence Collection)

```bash
# Against any public GitHub repo
python -m src.graph https://github.com/owner/repo-name

# With a PDF report
python -m src.graph https://github.com/owner/repo-name path/to/report.pdf
```

### Run as a module

```python
from src.graph import run_detective_audit

result = run_detective_audit(
    repo_url="https://github.com/owner/repo",
    pdf_path="reports/interim_report.pdf"
)

# Access evidence
for detective, evidences in result["evidences"].items():
    for ev in evidences:
        print(f"[{detective}] {ev.goal}: found={ev.found}, confidence={ev.confidence}")
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
│   └── interim_report.pdf    # Interim architectural report
├── audit/                    # Generated audit reports
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

## Status

| Layer | Status |
|---|---|
| Infrastructure (state, tools) | ✅ Complete |
| Detective Layer (RepoInvestigator, DocAnalyst, VisionInspector) | ✅ Complete |
| EvidenceAggregator (Fan-In) | ✅ Complete |
| Judicial Layer (Prosecutor, Defense, TechLead) | 🔄 Thursday |
| Chief Justice Synthesis | 🔄 Friday |
| Full End-to-End Report | 🔄 Saturday |
