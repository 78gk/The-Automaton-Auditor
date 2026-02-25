# Automaton Auditor — Interim Architecture Report
**FDE Challenge Week 2 | Interim Submission | Wednesday**

---

## Executive Summary

The **Automaton Auditor** is a production-grade hierarchical multi-agent swarm built with LangGraph, designed to perform forensic quality assurance on AI-generated codebases. It implements a **Digital Courtroom** metaphor: Detective agents collect objective forensic evidence, Judge agents debate that evidence through distinct adversarial personas, and a Chief Justice synthesizes a final deterministic verdict.

This interim report documents the architectural decisions made during Phase 0 (Infrastructure) and Phase 1/2 (Detective Layer + Forensic Tools), along with a concrete plan for the Judicial Layer and Synthesis Engine to be completed by Saturday.

---

## 1. Architecture Decisions

### 1.1 Why Pydantic Over Plain Dicts

**Decision:** All state objects — `Evidence`, `JudicialOpinion`, `CriterionResult`, `AuditReport`, and `AgentState` — use Pydantic `BaseModel` or `TypedDict` with strict field typing.

**Rationale:**
- **Schema Enforcement at Construction Time:** A `JudicialOpinion` with `score: int = Field(ge=1, le=5)` will raise a `ValidationError` immediately if a judge returns a score of 6 or "five". This prevents silent data corruption flowing downstream through the graph.
- **Parallel Safety with Annotated Reducers:** LangGraph requires explicit reducer functions when multiple parallel agents write to the same state key. We use:
  - `Annotated[Dict[str, List[Evidence]], operator.ior]` — dict union merge, so each Detective writes to its own key (`"repo"`, `"doc"`, `"vision"`) without overwriting others.
  - `Annotated[List[JudicialOpinion], operator.add]` — list extend, so each Judge appends its opinions without overwriting.
- **Self-Documenting API:** Pydantic models with `Field(description=...)` annotations serve as living documentation for every agent's expected input/output contract.

Without Pydantic, parallel agents writing plain dicts would cause silent overwrites — the last agent to finish would erase all previous agents' work.

### 1.2 Why AST Parsing Over Regex

**Decision:** `src/tools/repo_tools.py` uses Python's built-in `ast` module to analyze code structure, not regex.

**Rationale:**
- **Structural Verification:** Regex matches text patterns. AST matches code *structure*. A regex for `StateGraph` would match a comment `# StateGraph is not used here` or a string `"StateGraph"`. The AST visitor `GraphStructureVisitor` only matches when `StateGraph(AgentState)` is actually *instantiated as a call expression*.
- **Fan-Out Detection:** To detect parallel execution, we parse `builder.add_edge()` calls and build a graph of source→target relationships. Nodes with multiple outgoing edges are fan-out points; nodes with multiple incoming edges are fan-in points. This is impossible to determine reliably with regex.
- **Security:** AST parsing cannot be fooled by obfuscated strings or multi-line concatenations that regex would miss.

Implemented visitors:
- `GraphStructureVisitor` — detects `StateGraph`, `add_edge`, `add_conditional_edges`, `add_node`, fan-out/fan-in topology
- `PydanticModelVisitor` — detects `BaseModel` subclasses, `TypedDict` subclasses, `operator.add`/`operator.ior` usage
- `SecurityVisitor` — detects `os.system()` violations, `tempfile` usage, `subprocess.run()` usage

### 1.3 Sandboxing Strategy

**Decision:** All git clone operations use `tempfile.TemporaryDirectory()` as a sandbox context manager.

**Rationale:**
- The auditor clones *unknown, potentially hostile* repositories. Cloning into the live working directory risks:
  - Path traversal attacks (malicious `.git/hooks`)
  - Overwriting source files of the auditor itself
  - Leaving persistent artifacts on disk
- `tempfile.TemporaryDirectory()` creates an OS-managed isolated directory that is **automatically deleted** when the context exits, even on exception.
- `subprocess.run()` with `capture_output=True` is used instead of `os.system()` — this captures stdout/stderr, checks return codes, and never opens a shell.

```python
with tempfile.TemporaryDirectory() as tmp_dir:
    clone_target = str(Path(tmp_dir) / "repo")
    success, msg = clone_repo(repo_url, clone_target)
    # All analysis happens here — auto-cleaned on exit
```

### 1.4 RAG-Lite PDF Ingestion

**Decision:** `src/tools/doc_tools.py` uses `docling` for PDF parsing with a keyword-scored chunking retrieval (RAG-lite).

**Rationale:**
- PDFs can be large. Dumping the full text into an LLM context window is expensive and loses precision.
- We chunk the document into 1000-char overlapping segments and score each chunk by query term overlap. This is a lightweight TF-IDF-style approach that works without a vector database for documents of this size.
- `docling` handles complex PDFs with tables, images, and multi-column layouts — `pypdf` is included as a fallback.
- Image extraction uses `pypdf` page image objects for the VisionInspector pipeline.

---

## 2. Planned StateGraph Flow

```
START
  │
  ▼
ContextBuilder
  │  (loads rubric.json — the agent's Constitution)
  │
  ├────────────────────┬────────────────────┐
  ▼                    ▼                    ▼
RepoInvestigator   DocAnalyst         VisionInspector
(AST + Git)        (PDF + RAG)        (Diagrams)
  │                    │                    │
  └────────────────────┴────────────────────┘
                        │
                        ▼
               EvidenceAggregator  ← Fan-In sync point
               (cross-references PDF paths vs. repo files)
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Prosecutor     Defense       TechLead
     (adversarial)  (forgiving)   (pragmatic)
          │             │             │
          └─────────────┴─────────────┘
                        │
                        ▼
                  ChiefJustice
            (deterministic synthesis)
                        │
                        ▼
              Markdown Audit Report
                       END
```

**Key Parallel Patterns:**
- **Detective Fan-Out:** `ContextBuilder → [RepoInvestigator || DocAnalyst || VisionInspector]`
- **Detective Fan-In:** `[RepoInvestigator || DocAnalyst || VisionInspector] → EvidenceAggregator`
- **Judge Fan-Out:** `EvidenceAggregator → [Prosecutor || Defense || TechLead]`
- **Judge Fan-In:** `[Prosecutor || Defense || TechLead] → ChiefJustice`

---

## 3. Current Implementation Status (Interim)

### ✅ Completed (Wednesday)

| Component | File | Key Features |
|---|---|---|
| Typed State | `src/state.py` | Evidence, JudicialOpinion, CriterionResult, AuditReport, AgentState with reducers |
| Repo Tools | `src/tools/repo_tools.py` | Sandboxed clone, git log, AST graph/state/security analysis |
| Doc Tools | `src/tools/doc_tools.py` | docling PDF ingestion, RAG-lite query, hallucination detection |
| Detective Nodes | `src/nodes/detectives.py` | RepoInvestigator, DocAnalyst, VisionInspector, EvidenceAggregator |
| Detective Graph | `src/graph.py` | Parallel fan-out/fan-in StateGraph, rubric loading, CLI entry |
| Rubric | `rubric.json` | 10-dimension machine-readable constitution with synthesis rules |
| Judicial Stubs | `src/nodes/judges.py` | Full Prosecutor, Defense, TechLead implementation with distinct prompts |
| Synthesis Stub | `src/nodes/justice.py` | ChiefJustice with deterministic rules (security, fact, variance) |

### 🔄 Known Gaps & Completion Plan

| Gap | Plan | Target Day |
|---|---|---|
| Judges not yet wired into graph.py | Add fan-out from EvidenceAggregator to 3 judges | Thursday |
| ChiefJustice not wired to END | Add final node and Markdown serialization | Friday |
| VisionInspector runs but LLM call optional | Wire multimodal LLM for diagram classification | Friday |
| No self-audit report yet | Run agent against own repo | Saturday |
| No peer-audit report yet | Run agent against assigned peer's repo | Saturday |
| No interim PDF report images | Add architecture diagram | Wednesday (this doc) |

---

## 4. Forensic Evidence Collection Protocols Implemented

### Protocol A: RepoInvestigator

The `RepoInvestigator` node collects evidence for 7 forensic goals:

1. **`git_forensic_analysis`** — Runs `git log --format=%H|%ai|%s --reverse`, counts commits, detects bulk-upload pattern, scores progression (setup → tools → graph)
2. **`directory_structure`** — Scans all files, checks existence of 11 key expected paths
3. **`state_management_rigor`** — AST-parses `src/state.py`, verifies `BaseModel` subclasses, `TypedDict`, `operator.add`/`operator.ior` reducers
4. **`graph_orchestration`** — AST-parses `src/graph.py`, detects `StateGraph`, fan-out/fan-in topology, `add_conditional_edges`
5. **`safe_tool_engineering`** — AST-scans `src/tools/`, detects `tempfile`, flags `os.system()`, verifies `subprocess.run()`
6. **`structured_output_enforcement`** — AST-scans `src/nodes/judges.py`, detects `.with_structured_output()`, `bind_tools()`, persona names
7. **`chief_justice_synthesis`** — Reads `src/nodes/justice.py`, checks for deterministic rule keywords

### Protocol B: DocAnalyst

The `DocAnalyst` node collects evidence for 3 forensic goals:

1. **`theoretical_depth`** — Searches for "Dialectical Synthesis", "Fan-In/Fan-Out", "Metacognition", "State Synchronization"; distinguishes substantive explanations from keyword drops
2. **`report_accuracy`** — Extracts all `src/...` file paths from the PDF text for later cross-reference
3. **`doc_<criterion>`** — RAG-lite queries for specific concepts per rubric dimension

### Protocol C: EvidenceAggregator (Fan-In)

Cross-references paths mentioned in the PDF against files actually found in the repo, producing a **hallucination rate** metric and flagging `Hallucinated Paths`.

---

## 5. Dialectical Synthesis — Judicial Layer Design

The Judicial Layer implements **Thesis-Antithesis-Synthesis** through three adversarial personas with strictly non-colluding system prompts:

### The Prosecutor (Adversarial)
- Core philosophy: "Trust No One. Assume Vibe Coding."
- Charges: "Orchestration Fraud", "Hallucination Liability", "Security Negligence", "Process Fraud"
- Scoring bias: 1–3 range, harsh, requires concrete proof for any credit

### The Defense (Optimistic)
- Core philosophy: "Reward Effort and Intent. Look for the Spirit of the Law."
- Mitigations: boosts score for sophisticated AST logic despite broken graph, rewards iteration in git history
- Scoring bias: 3–5 range, generous, argues for partial credit

### The Tech Lead (Pragmatic)
- Core philosophy: "Does it actually work? Is it maintainable?"
- Role: tie-breaker between extremes, 2x weight on architecture criteria in ChiefJustice
- Scoring bias: realistic 1–5, specific remediation advice

**Anti-Persona-Collusion:** The three system prompts share <10% text overlap. Each has distinct scoring instructions, distinct vocabulary, and explicitly different philosophies.

---

## 6. Chief Justice — Deterministic Synthesis Rules

The `ChiefJusticeNode` in `src/nodes/justice.py` uses **hardcoded Python if/else logic**, not LLM averaging:

| Rule | Trigger | Effect |
|---|---|---|
| **Rule of Security** | `os.system()` detected by Prosecutor | Score capped at 3, overrides Defense effort points |
| **Rule of Evidence (Fact Supremacy)** | Detective: artifact missing (confidence >70%) AND Defense claims it exists | Defense score adjusted down to ≤2 |
| **Rule of Functionality** | Architecture criteria (`graph_orchestration`, `state_management_rigor`, etc.) | Tech Lead score counted 2x in weighted average |
| **Variance Rule** | Score variance across 3 judges > 2 | `dissent_summary` field required in `CriterionResult` |
| **Variance Re-evaluation** | Same trigger as above | Re-evaluate citing specific evidence from each judge before final score |

---

## 7. Rubric Integration

The `rubric.json` file serves as the agent's **Constitution** — loaded at runtime by `ContextBuilder` and distributed to agents:

- **Detectives** filter by `target_artifact` (`github_repo`, `pdf_report`, `pdf_images`)
- **Judges** receive `judicial_logic` from their matching dimension
- **ChiefJustice** uses `synthesis_rules` from the JSON top-level key

This allows updating the Constitution (e.g., adding new forensic protocols) without redeploying agent code.

---

## 8. Remediation Plan for Known Gaps

### Priority 1 — Wire Judicial Layer (Thursday)
- Update `src/graph.py` to add `Prosecutor`, `Defense`, `TechLead` nodes
- Add fan-out edges: `EvidenceAggregator → [Prosecutor, Defense, TechLead]`
- Add fan-in edges: `[Prosecutor, Defense, TechLead] → ChiefJustice`
- Add `ChiefJustice → END`

### Priority 2 — Markdown Report Output (Friday)
- Finalize `_serialize_to_markdown()` in `justice.py`
- Add conditional edges for error handling (failed clone → skip to report with error)
- Test end-to-end with a real repo URL

### Priority 3 — Self & Peer Audit (Saturday)
- Run agent against own repo: `python -m src.graph https://github.com/78gk/The-Automaton-Auditor`
- Run agent against peer's repo
- Record 5-minute video demo
- Write final reflection on MinMax feedback loop

---

*Report generated: Wednesday, 2026-02-25*
*Repository: https://github.com/78gk/The-Automaton-Auditor*
