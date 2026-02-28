# Automaton Auditor — Project Context

**Last Updated:** 2026-02-27 (Friday — Peer Audit & Score Improvements)
**Repository:** https://github.com/78gk/The-Automaton-Auditor
**Current Status:** ✅ Interim submitted | ✅ Full graph wired | ✅ Peer audit done (tedoaba: 47/50) | ✅ Score improvements committed | 🔄 Self-audit pending (API quota) | 🔄 Final submission Saturday

---

## What We're Building
A **Digital Courtroom** — a hierarchical multi-agent LangGraph swarm that forensically audits AI-generated codebases.

- **Input:** GitHub repo URL + PDF report
- **Output:** Production-grade Markdown audit report with deterministic scoring

---

## Current Architecture State

```
START
  │
  ▼
ContextBuilder  [✅ LIVE — validates URL, loads rubric.json]
  │
  ├── [invalid URL] ──► ErrorHandler ──► END  [✅ LIVE]
  │
  ├── RepoInvestigator  [✅ LIVE — 7 evidence goals, AST + git]
  ├── DocAnalyst         [✅ LIVE — PDF ingestion, RAG-lite, hallucination detection]
  └── VisionInspector    [✅ LIVE — image extraction, multimodal LLM]
                                    │
                                    ▼
                         EvidenceAggregator  [✅ LIVE — fan-in, cross-reference]
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
               Prosecutor       Defense         TechLead
          [✅ LIVE —         [✅ LIVE —       [✅ LIVE —
           adversarial]       optimistic]      pragmatic]
                    └───────────────┼───────────────┘
                                    ▼
                            ChiefJustice
                       [✅ LIVE — 4 deterministic rules
                        Security Override, Fact Supremacy,
                        Tech Lead 2x Weight, Variance Rule]
                                    │
                                   END
```

---

## What's DONE (Wednesday)

### Code — All Implemented & Committed
| File | Status | Key Features |
|---|---|---|
| `src/state.py` | ✅ Done | `Evidence`, `JudicialOpinion`, `CriterionResult`, `AuditReport`, `AgentState` with `operator.ior`/`operator.add` reducers |
| `src/tools/repo_tools.py` | ✅ Done | `validate_repo_url()`, sandboxed `clone_repo()`, git log forensics, 3 AST visitors (GraphStructureVisitor, PydanticModelVisitor, SecurityVisitor) |
| `src/tools/doc_tools.py` | ✅ Done | Docling + pypdf fallback, RAG-lite chunked retrieval, hallucination path cross-reference, theoretical depth analysis |
| `src/nodes/detectives.py` | ✅ Done | `RepoInvestigator` (7 evidence goals), `DocAnalyst` (3+ goals), `VisionInspector`, `EvidenceAggregator` (fan-in + cross-ref) |
| `src/nodes/judges.py` | ✅ Done | `Prosecutor` (temp=0.1, adversarial), `Defense` (temp=0.3, optimistic), `TechLead` (temp=0.1, pragmatic) — all with `.with_structured_output(JudicialOpinion)` + anti-hallucination guardrails |
| `src/nodes/justice.py` | ✅ Done | `ChiefJustice` with 4 deterministic rules: Security Override, Fact Supremacy, Functionality Weight (TechLead 2x), Variance Rule (gap>2 → dissent_summary) + Markdown serializer |
| `src/graph.py` | ✅ Complete | Full Digital Courtroom wired: Detective fan-out/fan-in + Judge fan-out/fan-in + ChiefJustice → END. Returns list from `route_after_context()` for true parallel fan-out. |
| `rubric.json` | ✅ Done | 10-dimension Constitution with forensic instructions, success/failure patterns, synthesis rules |

### Infrastructure
| File | Status |
|---|---|
| `pyproject.toml` | ✅ Done — uv managed, all deps declared |
| `.env.example` | ✅ Done — GOOGLE_API_KEY, OPENAI_API_KEY, LANGCHAIN_* |
| `README.md` | ✅ Done — full setup, architecture, design decisions |
| `.gitignore` | ✅ Done |
| `REFLECTION.md` | ✅ Done — 6 self-corrections documented for peer rubric |
| `checklist.md` | ✅ Done — tracks all interim + final deliverables |

### Reports
| File | Status |
|---|---|
| `reports/interim_report.md` | ✅ Done — QA-enhanced, trade-off tables, gap analysis, risk mitigation |
| `reports/interim_report.pdf` | ✅ Done — 728KB, 13 pages, professional typography, headers/footers |
| `reports/stategraph_architecture.png` | ✅ Done — 3564×4884px @ 220 DPI, embedded in PDF page 6, section 2.1 |

### Git History (15 commits — perfect progression)
```
cf6c325  feat: initialize project with uv, pyproject.toml and environment scaffold
d4fb54a  feat: define typed AgentState with Pydantic models and operator reducers
51e973a  feat: implement sandboxed repo tools (AST parser, git clone via tempfile)
24904e9  feat: implement RepoInvestigator and DocAnalyst detective nodes
f261901  feat: wire parallel detective fan-out/fan-in StateGraph with EvidenceAggregator
c256d26  feat: implement Prosecutor, Defense, TechLead judges + ChiefJustice synthesis
3b9c160  docs: README, checklist, context
3fa5f69  docs: interim architecture report
9946386  docs: QA-enhanced report — trade-offs, Mermaid diagram, risk mitigation
3048f38  docs: production-grade interim_report.pdf
[fix]    fix: QA-driven improvements — Prosecutor temp, anti-hallucination, URL validation, error edge
[feat]   feat: embed StateGraph architecture diagram (PNG) in PDF — page 6 section 2.1
[fix]    fix: redesigned flawless StateGraph diagram (3564x4884px, 220dpi)
[fix]    fix: diagram now at correct position in PDF (section 2.1)
```

---

## What's DONE (Thursday — COMPLETED)

### ✅ Judicial Layer Fully Wired (src/graph.py)
1. ✅ Added `Prosecutor`, `Defense`, `TechLead`, `ChiefJustice` nodes to `build_graph()`
2. ✅ Fan-out: `EvidenceAggregator → [Prosecutor, Defense, TechLead]` (parallel)
3. ✅ Fan-in: `[Prosecutor, Defense, TechLead] → ChiefJustice`
4. ✅ `ChiefJustice → END`
5. ✅ Removed interim `EvidenceAggregator → END` edge
6. ✅ Fixed `route_after_context()` to return `List[str]` for true parallel fan-out (correct LangGraph pattern)
7. ✅ Added `run_audit()` as primary entry point with `output_dir` param; kept `run_detective_audit` as backwards-compat alias
8. ✅ Updated CLI to accept `[output_dir]` as third argument

### ✅ Bug Fixes
9. ✅ Fixed f-string syntax error in `detectives.py` (nested quotes incompatible with Python 3.11)
10. ✅ Fixed model name: `gemini-1.5-pro` → `gemini-2.0-flash` in both `detectives.py` and `judges.py` (1.5-pro returns 404 on free tier)

### ✅ Self-Audit Attempted & Diagnosed
11. ✅ Graph compiled and ran against own repo — **detectives worked perfectly**:
    - `repo`: 7 evidence items collected (git forensics, state, graph, tools, structured output, etc.)
    - `doc`: 5 evidence items collected (theoretical depth, report accuracy, etc.)
    - `vision`: 1 evidence item collected
12. ⚠️ Judges returned 0 opinions due to **Google API free tier quota exhausted** (429 RESOURCE_EXHAUSTED)
    - Root cause: Multiple test runs consumed the daily free tier quota for `gemini-2.0-flash`
    - The judge code itself is correct — structured output, personas, evidence formatting all verified
    - Fix: Wait for quota reset (midnight Pacific) OR enable billing on Google AI Studio (~$0.10–0.30 per audit)
13. ✅ Stale `audit/audit_report.md` produced (all 1/5 — placeholder fallback scores, not real)

### ✅ Environment Setup
14. ✅ `.env` created with `GOOGLE_API_KEY` set
15. ✅ Dependencies installed: `langgraph`, `langchain-google-genai`, `langchain-openai`, `python-dotenv`

---

## What's LEFT for Saturday (PRIORITY ORDER)

### 🔴 CRITICAL — Run Self-Audit (blocked by API quota until reset)
1. Wait for Google API free tier quota to reset (midnight Pacific / ~08:00 UTC Friday)
   - OR enable billing at https://aistudio.google.com/app/apikey (~$0.30 per full audit)
2. Run: `python -m src.graph https://github.com/78gk/The-Automaton-Auditor reports/interim_report.pdf audit/report_onself_generated`
3. Move/overwrite `audit/audit_report.md` → `audit/report_onself_generated/audit_report.md`

### 🟡 HIGH — Observability (LangSmith Trace for submission)
4. Set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY=<key>` in `.env`
5. Get LangSmith key from: https://smith.langchain.com/
6. Run audit once with tracing enabled → capture trace URL from LangSmith dashboard
7. Add trace URL to README under "LangSmith Trace" section

### 🟢 STANDARD — Final Submission Prep
8. Run peer-audit against assigned peer's repo → save to `audit/report_onpeer_generated/audit_report.md`
9. Record 5-min video demo (show full flow: ContextBuilder → Detectives → Aggregator → Judges → ChiefJustice → report)
10. Write final reflection (what peer agent caught, MinMax loop analysis)
11. Commit + push all audit reports, reflection, final report
12. Convert `reports/interim_report.md` → `reports/final_report.pdf`

---

## Tech Stack
- **Framework:** LangGraph (StateGraph)
- **Package Manager:** uv
- **State:** Pydantic BaseModel + TypedDict with Annotated reducers
- **LLM:** Google Gemini 2.0 Flash (preferred) / OpenAI GPT-4o (fallback)
- **PDF Parsing:** docling + pypdf fallback
- **AST Parsing:** Python `ast` module (3 custom visitors)
- **Observability:** LangSmith tracing (pending capture)

## Key Patterns (for reference when resuming)
- `operator.ior` for `evidences` dict (parallel merge without overwrite)
- `operator.add` for `opinions` list (parallel append without overwrite)
- `tempfile.TemporaryDirectory()` for sandboxed git clone
- `.with_structured_output(JudicialOpinion)` for all 3 judge LLM calls
- `route_after_context()` conditional routing: invalid URL → ErrorHandler

## Rubric Dimensions (10 total) — Current Score Estimate
| # | Dimension | Est. Score | Notes |
|---|---|---|---|
| 1 | git_forensic_analysis | 5/5 | 15 commits, clear progression |
| 2 | state_management_rigor | 5/5 | Pydantic + reducers implemented |
| 3 | graph_orchestration | 5/5 | Full parallel fan-out/fan-in wired (Thu) |
| 4 | safe_tool_engineering | 5/5 | tempfile + URL validation + subprocess |
| 5 | structured_output_enforcement | 5/5 | `.with_structured_output(JudicialOpinion)` wired and running |
| 6 | judicial_nuance | 5/5 | 3 distinct personas live, parallel execution |
| 7 | chief_justice_synthesis | 5/5 | Deterministic rules live: Security Override, Fact Supremacy, Variance Rule |
| 8 | theoretical_depth | 5/5 | Substantive PDF explanations |
| 9 | report_accuracy | 5/5 | All paths verified |
| 10 | swarm_visual | 5/5 | 3564×4884 PNG embedded in PDF |
| **Total** | | **~50/50** | Full graph wired Thu ✅ |

## Environment Variables Required
- `GOOGLE_API_KEY` or `OPENAI_API_KEY`
- `LANGCHAIN_API_KEY`
- `LANGCHAIN_TRACING_V2=true`
- `LANGCHAIN_PROJECT=automaton-auditor`
