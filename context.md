# Automaton Auditor — Project Context

**Last Updated:** 2026-02-25 (Wednesday — Interim Submission Day)
**Repository:** https://github.com/78gk/The-Automaton-Auditor
**Current Status:** ✅ Interim submitted | 🔄 Resuming Thursday

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
          [✅ IMPLEMENTED    [✅ IMPLEMENTED  [✅ IMPLEMENTED
           🔄 NOT WIRED]      🔄 NOT WIRED]   🔄 NOT WIRED]
                    └───────────────┼───────────────┘
                                    ▼
                            ChiefJustice
                       [✅ IMPLEMENTED — 4 deterministic rules
                        🔄 NOT WIRED]
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
| `src/graph.py` | ✅ Partial | Detective fan-out/fan-in wired. Conditional ErrorHandler edge. **Judges + ChiefJustice NOT YET wired** |
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

## What's LEFT for Thursday (PRIORITY ORDER)

### 🔴 CRITICAL — Wire Judicial Layer into graph.py
1. Add `Prosecutor`, `Defense`, `TechLead` nodes to `build_graph()`
2. Add fan-out edges: `EvidenceAggregator → [Prosecutor, Defense, TechLead]`
3. Add fan-in edges: `[Prosecutor, Defense, TechLead] → ChiefJustice`
4. Add `ChiefJustice → END`
5. Remove interim `EvidenceAggregator → END` edge
6. Test `graph.invoke()` with this repo URL

### 🟡 HIGH — Observability
7. Set `LANGCHAIN_TRACING_V2=true` in `.env`, run once, capture LangSmith trace URL
8. Add trace URL to README

### 🟢 STANDARD — Final Submission Prep (Saturday)
9. Run self-audit: `python -m src.graph https://github.com/78gk/The-Automaton-Auditor`
10. Save output to `audit/report_onself_generated/audit_report.md`
11. Run peer-audit against assigned peer repo
12. Save to `audit/report_onpeer_generated/audit_report.md`
13. Record 5-min video demo
14. Write final reflection
15. Commit + push everything
16. Convert final report to PDF

---

## Tech Stack
- **Framework:** LangGraph (StateGraph)
- **Package Manager:** uv
- **State:** Pydantic BaseModel + TypedDict with Annotated reducers
- **LLM:** Google Gemini 1.5 Pro (preferred) / OpenAI GPT-4o (fallback)
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
| 3 | graph_orchestration | 3/5 | Detective parallel done; judges not wired yet |
| 4 | safe_tool_engineering | 5/5 | tempfile + URL validation + subprocess |
| 5 | structured_output_enforcement | 4/5 | Code ready, not wired |
| 6 | judicial_nuance | 4/5 | 3 distinct personas, not running yet |
| 7 | chief_justice_synthesis | 4/5 | Deterministic rules coded, not wired |
| 8 | theoretical_depth | 5/5 | Substantive PDF explanations |
| 9 | report_accuracy | 5/5 | All paths verified |
| 10 | swarm_visual | 5/5 | 3564×4884 PNG embedded in PDF |
| **Total** | | **~45/50** | Remaining 5 pts from wiring judges Thu |

## Environment Variables Required
- `GOOGLE_API_KEY` or `OPENAI_API_KEY`
- `LANGCHAIN_API_KEY`
- `LANGCHAIN_TRACING_V2=true`
- `LANGCHAIN_PROJECT=automaton-auditor`
