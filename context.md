# Automaton Auditor — Project Context

## What We're Building
A **Digital Courtroom** — a hierarchical multi-agent LangGraph swarm that forensically audits AI-generated codebases.

- **Input:** GitHub repo URL + PDF report
- **Output:** Production-grade Markdown audit report

## Architecture

```
START
  ├── RepoInvestigator (parallel) ──────────────┐
  ├── DocAnalyst (parallel) ────────────────────┤
  └── VisionInspector (parallel, optional) ──────┤
                                                  ▼
                                        EvidenceAggregator
                                                  │
                                    ┌─────────────┼─────────────┐
                                    ▼             ▼             ▼
                               Prosecutor     Defense       TechLead
                                    └─────────────┼─────────────┘
                                                  ▼
                                          ChiefJustice
                                                  │
                                                 END
```

## Tech Stack
- **Framework:** LangGraph (StateGraph)
- **Package Manager:** uv
- **State:** Pydantic BaseModel + TypedDict with Annotated reducers
- **LLM:** Google Gemini / OpenAI GPT-4o
- **PDF Parsing:** docling
- **AST Parsing:** Python `ast` module
- **Observability:** LangSmith tracing

## Key Patterns
- `operator.ior` for `evidences` dict (parallel merge without overwrite)
- `operator.add` for `opinions` list (parallel append without overwrite)
- `tempfile.TemporaryDirectory()` for sandboxed git clone
- `.with_structured_output(JudicialOpinion)` for judges

## Rubric Dimensions (10 total)
1. git_forensic_analysis (github_repo)
2. state_management_rigor (github_repo)
3. graph_orchestration (github_repo)
4. safe_tool_engineering (github_repo)
5. structured_output_enforcement (github_repo)
6. judicial_nuance (github_repo)
7. chief_justice_synthesis (github_repo)
8. theoretical_depth (pdf_report)
9. report_accuracy (pdf_report)
10. swarm_visual (pdf_images)

## Environment Variables Required
- `GOOGLE_API_KEY` or `OPENAI_API_KEY`
- `LANGCHAIN_API_KEY`
- `LANGCHAIN_TRACING_V2=true`
- `LANGCHAIN_PROJECT`

## Git Strategy (for rubric compliance)
Commit history must show progression:
1. "feat: initialize project with uv and pyproject.toml"
2. "feat: define typed state with Pydantic models and reducers"
3. "feat: implement sandboxed repo tools with AST parser"
4. "feat: implement doc tools with PDF ingestion"
5. "feat: implement detective nodes (RepoInvestigator, DocAnalyst)"
6. "feat: wire parallel detective graph with fan-out/fan-in"
