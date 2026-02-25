# Development Reflection — Automaton Auditor
**FDE Challenge Week 2 | Self-Feedback Loop Documentation**
**Repository:** https://github.com/78gk/The-Automaton-Auditor

---

## Purpose

This document demonstrates the **self-feedback loop** required by the Peer-Gradable rubric:
proactive communication of what was learned, what was corrected, and why — not just what was built.

---

## Phase 1 Reflection (Wednesday — Interim Submission)

### What I Built
The full Detective Layer infrastructure for the Automaton Auditor:
- `src/state.py` — Pydantic-typed state with parallel-safe `operator.ior`/`operator.add` reducers
- `src/tools/repo_tools.py` — Sandboxed AST-based forensic analysis (3 visitor classes)
- `src/tools/doc_tools.py` — Docling PDF ingestion with RAG-lite retrieval
- `src/nodes/detectives.py` — 3 parallel detective agents + EvidenceAggregator
- `src/graph.py` — LangGraph StateGraph with fan-out/fan-in + conditional error routing
- `src/nodes/judges.py` — Judicial layer (implemented, pending graph wiring)
- `src/nodes/justice.py` — Chief Justice synthesis engine (implemented, pending wiring)

### Key Architectural Insights Gained

**1. Pydantic reducers prevent silent data loss in parallel graphs.**
Before building, I assumed parallel LangGraph nodes would naturally merge state. In practice, without `Annotated[Dict, operator.ior]`, the last Detective to finish would overwrite all previous Detectives' evidence. This would be a completely silent failure — no exception, no warning, just missing data. The fix is non-obvious and not in the basic LangGraph docs.

**2. AST parsing is architecturally superior to regex for code forensics.**
I initially considered regex for detecting `StateGraph` usage. The flaw: regex matches text, not structure. A comment `# StateGraph is slow` would match. A variable named `not_a_StateGraph` would match. AST visitors match only actual call expressions in the parse tree — a fundamentally different level of verification.

**3. Sandboxing is a security requirement, not optional.**
Cloning unknown repos into the working directory exposes the auditor to path traversal via malicious `.git/hooks`. `tempfile.TemporaryDirectory()` combined with `subprocess.run()` (not `os.system()`) is the correct pattern. I implemented URL validation as an additional layer.

**4. The rubric itself should be the agent's Constitution.**
Loading `rubric.json` at runtime (not hardcoding dimensions in agent prompts) means the auditor's evaluation criteria can be updated without redeploying code. Each detective filters by `target_artifact`, each judge receives `judicial_logic` for their dimension. This was a design decision that emerged from thinking about the rubric as data, not code.

---

## Self-Critique & Corrections Applied

The following gaps were identified through internal QA audit and immediately corrected:

### Correction 1: Prosecutor Temperature
**Identified:** Prosecutor LLM called with `temperature=0.2` — slightly too creative for an adversarial agent.
**Corrected:** Changed to `temperature=0.1` — the Prosecutor must be deterministic and harsh, not creative.
**File:** `src/nodes/judges.py` → `prosecutor_node()`
**Commit:** `fix: set Prosecutor temperature to 0.1 and add anti-hallucination guardrails`

### Correction 2: Defense Anti-Hallucination Guardrail
**Identified:** Defense prompt allowed generous arguments without requiring evidence citation.
This creates a vulnerability: Defense could fabricate artifacts to boost scores.
**Corrected:** Added explicit guardrail: "You may ONLY cite evidence items listed in the Forensic Evidence Summary. Do NOT fabricate or assume the existence of artifacts not listed there."
**File:** `src/nodes/judges.py` → `DEFENSE_SYSTEM_PROMPT`

### Correction 3: Prosecutor Evidence Grounding
**Identified:** Similar issue — Prosecutor could cite non-existent violations.
**Corrected:** Added: "ONLY reference evidence items listed in the Forensic Evidence Summary. Do not invent evidence."
**File:** `src/nodes/judges.py` → `PROSECUTOR_SYSTEM_PROMPT`

### Correction 4: URL Input Validation (Security)
**Identified:** `clone_repo()` accepted any string as a URL — potential shell injection vector even with `subprocess.run()` (malformed URLs can cause git to misinterpret arguments).
**Corrected:** Added `validate_repo_url()` with regex allowlist pattern + dangerous character blocklist.
**File:** `src/tools/repo_tools.py`

### Correction 5: Conditional Error Edge Missing
**Identified:** Graph had no error routing — an invalid URL would propagate as a clone failure inside `RepoInvestigator` but the graph would still attempt `DocAnalyst` and `VisionInspector`.
**Corrected:** Added `ErrorHandler` node + `route_after_context()` conditional function. Invalid URL now terminates gracefully before fan-out.
**File:** `src/graph.py`

### Correction 6: Criterion-Priority Focus in Judge Prompts
**Identified:** All three judges evaluated all criteria with equal intensity — not aligned with their personas.
**Corrected:** Added `CRITERION PRIORITIES` sections to each judge prompt. Prosecutor focuses hardest on `safe_tool_engineering` and `git_forensic_analysis`. Defense focuses hardest on `theoretical_depth` and `judicial_nuance`.
**File:** `src/nodes/judges.py`

---

## What I Would Do Differently

1. **Start with the rubric as data from day 1.** I built the state schema first, then realized the rubric should drive the agents. The `rubric.json` Constitution approach should be the first architectural decision.

2. **Wire the graph incrementally, testing each node as added.** I built all nodes before wiring — this means I can't test the graph until Thursday. A better approach: wire + test `ContextBuilder → RepoInvestigator → END` first, then add `DocAnalyst`, then `VisionInspector`, etc.

3. **Add URL validation to the very first clone attempt.** Security should not be an afterthought caught in QA. Input validation belongs at the entry point.

---

## Thursday Plan (Feedback-Driven)

Based on the gaps identified:

1. Wire `Prosecutor`, `Defense`, `TechLead` nodes into `graph.py`
2. Wire `ChiefJustice` as the final synthesis node
3. Test full `graph.invoke()` against this repo
4. Capture LangSmith trace URL
5. Verify `dissent_summary` generates correctly for criteria with score variance > 2

---

## Communication of Known Limitations

The following limitations are acknowledged and will be addressed in the final submission:

| Limitation | Impact | Mitigation |
|---|---|---|
| Judges not yet graph-wired | No end-to-end judicial verdict yet | Wiring Thursday — all judge code is ready |
| VisionInspector LLM requires API key | Diagram analysis may skip | Evidence item defaults to `found=False` with clear rationale |
| RAG-lite uses keyword overlap, not embeddings | Lower semantic precision | Sufficient for forensic keyword detection at this scale |
| No LangSmith trace yet | Observability unverified | Will be captured during Thursday end-to-end test |

---

*Reflection version: 1.0 | Date: 2026-02-25 | Author: github.com/78gk*
