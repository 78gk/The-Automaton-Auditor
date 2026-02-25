# Automaton Auditor — Interim Submission Checklist
**Due: Wednesday 21:00 UTC | Status: IN PROGRESS**

## Interim Deliverables (Wednesday)

### Code Files
- [ ] `src/state.py` — Pydantic/TypedDict state definitions (Evidence, JudicialOpinion, AgentState) with reducers
- [ ] `src/tools/repo_tools.py` — Sandboxed git clone (tempfile), git log, AST-based graph structure analysis
- [ ] `src/tools/doc_tools.py` — PDF ingestion and chunked querying (RAG-lite)
- [ ] `src/nodes/detectives.py` — RepoInvestigator and DocAnalyst as LangGraph nodes outputting Evidence objects
- [ ] `src/graph.py` — Partial StateGraph: Detectives in parallel (fan-out) + EvidenceAggregator (fan-in)

### Infrastructure
- [ ] `pyproject.toml` — Managed by uv
- [ ] `.env.example` — All required API keys listed (no secrets)
- [ ] `README.md` — Setup, install, and run instructions

### Reports
- [ ] `reports/interim_report.pdf` — Architecture decisions, known gaps, planned judicial layer, StateGraph diagram

### Repository
- [ ] `rubric.json` — Machine-readable rubric for agents
- [ ] Git repo initialized with meaningful commit history (>3 commits, progression story)
- [ ] Pushed to GitHub

## Final Deliverables (Saturday)
- [ ] `src/nodes/judges.py` — Prosecutor, Defense, TechLead with distinct prompts + structured output
- [ ] `src/nodes/justice.py` — ChiefJusticeNode with deterministic conflict resolution
- [ ] `src/graph.py` — Complete graph with judge fan-out, conditional edges, end-to-end flow
- [ ] `audit/report_onself_generated/` — Self-audit markdown report
- [ ] `audit/report_onpeer_generated/` — Peer-audit markdown report
- [ ] `audit/report_bypeer_received/` — Peer's report on our repo
- [ ] `reports/final_report.pdf`
- [ ] LangSmith trace link
- [ ] Video demo (5 min)
