# Automaton Auditor — Submission Checklist
**Repo: https://github.com/78gk/The-Automaton-Auditor**
**Interim Due: Wednesday 21:00 UTC | Status: ✅ SUBMITTED**
**Final Due: Saturday 21:00 UTC | Status: 🔄 IN PROGRESS**

---

## Interim Deliverables (Wednesday) — ✅ ALL COMPLETE

### Code Files
- [x] `src/state.py` — Pydantic BaseModel (Evidence, JudicialOpinion, CriterionResult, AuditReport) + TypedDict AgentState with `operator.ior`/`operator.add` reducers
- [x] `src/tools/repo_tools.py` — Sandboxed git clone (`tempfile`), URL validation, git log forensics, 3 AST visitor classes (GraphStructureVisitor, PydanticModelVisitor, SecurityVisitor)
- [x] `src/tools/doc_tools.py` — Docling PDF ingestion + `pypdf` fallback, RAG-lite chunked retrieval, hallucination path cross-reference
- [x] `src/nodes/detectives.py` — RepoInvestigator (7 evidence items), DocAnalyst (3+ evidence items), VisionInspector, EvidenceAggregator (fan-in + cross-reference)
- [x] `src/graph.py` — Parallel fan-out/fan-in StateGraph with conditional error edge (ErrorHandler for invalid URLs)

### Infrastructure
- [x] `pyproject.toml` — Managed by uv, all dependencies declared
- [x] `.env.example` — GOOGLE_API_KEY, OPENAI_API_KEY, LANGCHAIN_* all documented
- [x] `README.md` — Full setup, architecture diagram, design decision explanations, status table

### Reports
- [x] `reports/interim_report.md` — Full QA-enhanced architecture report with trade-off tables, Mermaid diagram, gap analysis, risk mitigation
- [x] `reports/interim_report.pdf` — Professional PDF (37KB) with headers/footers, typography, metadata

### Repository
- [x] `rubric.json` — 10-dimension machine-readable Constitution with synthesis rules
- [x] Git repo: 10 commits with clear progression story (setup → state → tools → detectives → judges → justice → docs → report → QA → PDF)
- [x] Pushed to GitHub: https://github.com/78gk/The-Automaton-Auditor

### QA Fixes Applied (Post-Audit)
- [x] Prosecutor temperature fixed: 0.2 → 0.1 (most skeptical, least creative)
- [x] Defense anti-hallucination guardrail added (cite only listed evidence)
- [x] Prosecutor criterion-priority focus areas added
- [x] URL validation added to `clone_repo()` — blocks shell injection
- [x] Conditional error edge added to graph: ContextBuilder → ErrorHandler → END
- [x] `REFLECTION.md` added — self-feedback loop documentation

---

## Final Deliverables (Saturday) — 🔄 SCHEDULED

### Code Files (Implemented, Not Yet Wired)
- [x] `src/nodes/judges.py` — Prosecutor, Defense, TechLead with distinct prompts + `.with_structured_output(JudicialOpinion)` *(implemented, wiring Thu)*
- [x] `src/nodes/justice.py` — ChiefJustice with 4 deterministic rules (security, fact supremacy, functionality weight, variance) + Markdown serializer *(implemented, wiring Thu)*
- [ ] `src/graph.py` — Complete graph with judge fan-out, ChiefJustice fan-in, conditional edges end-to-end *(Thursday)*

### Audit Reports
- [ ] `audit/report_onself_generated/audit_report.md` — Self-audit *(Saturday AM)*
- [ ] `audit/report_onpeer_generated/audit_report.md` — Peer-audit *(Saturday PM)*
- [ ] `audit/report_bypeer_received/` — Peer's report on our repo *(Saturday)*

### Submission Materials
- [ ] `reports/final_report.pdf` — Full architecture + results report *(Saturday)*
- [ ] LangSmith trace URL — Full graph execution trace *(Friday)*
- [ ] Video demo (5 min) — Graph execution, evidence summary, final report *(Saturday)*
