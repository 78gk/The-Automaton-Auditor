# Implementation Guide: The Automaton Auditor
**Target Workflow:** Fast-track for Interim (Wed) and Final (Sat) Submissions.
**System Role:** Senior Full-Stack Developer & Technical Strategist.

---

## 1. Project Definition & Critical Concepts

### Project Synthesis
The **Automaton Auditor** is a hierarchical multi-agent swarm built with LangGraph designed to perform forensic quality assurance on AI-generated codebases. It utilizes a **Detective Layer** for objective evidence collection (AST parsing, Git logs, PDF analysis) and a **Judicial Layer** (Prosecutor, Defense, Tech Lead) to debate project quality based on a strict 10-dimension rubric. A deterministic **Chief Justice** node synthesizes these adversarial viewpoints into a production-grade Markdown audit report with actionable remediation steps.

### 5 Critical Concepts for Mastery
1. **Parallel Hierarchical Orchestration:** Using LangGraph's `fan-out` and `fan-in` patterns to run specialized agents concurrently without state collisions.
2. **Forensic Evidence (AST vs. Regex):** Relying on Python’s `ast` module to verify the *existence and structure* of code (e.g., verifying `StateGraph` wiring) rather than brittle text matching.
3. **Dialectical Synthesis:** Implementing the "Thesis-Antithesis-Synthesis" model where distinct personas (Prosecutor/Defense) argue over the same evidence to ensure nuanced grading.
4. **Typed State Management:** Utilizing Pydantic `BaseModel` and `Annotated` reducers (`operator.add`, `operator.ior`) to ensure the swarm's state is strictly validated and additive.
5. **Deterministic Governance:** Hardcoding "Constitutional Rules" in the final synthesis node to ensure facts (detectives) and safety (security) always override subjective opinions (judges).

---

## 2. Fast-Track Implementation Timeline

### **Day 3 (TODAY - WEDNESDAY): Interim Submission Sprint**
*   **Deadline:** 21:00 UTC
*   **Focus:** Infrastructure & Forensic Detectives (Phase 0-1)
*   **Key Tasks:** 
    *   Scaffold workspace with `uv`.
    *   Define `src/state.py` (Pydantic models for Evidence, Opinions, State).
    *   Build `src/tools/repo_tools.py` (Sandboxed Git + AST Parser).
    *   Build `src/tools/doc_tools.py` (PDF Parser).
    *   Wire `src/graph.py` with parallel Detective nodes + Aggregator.
*   **Interim Deliverable:** Working graph that clones a repo and extracts structured JSON evidence.

### **Day 4 (THURSDAY): The Dialectical Bench**
*   **Focus:** Parallel Judicial Nodes (Phase 3)
*   **Key Tasks:**
    *   Implement `src/nodes/judges.py` with Prosecutor, Defense, and Tech Lead personas.
    *   Enforce structured output using `.with_structured_output(JudicialOpinion)`.
    *   Parallelize judge execution in the graph for each rubric dimension.

### **Day 5 (FRIDAY): The Supreme Court & Serialization**
*   **Focus:** Synthesis Engine & Markdown Reporting (Phase 4)
*   **Key Tasks:**
    *   Implement `src/nodes/justice.py` with deterministic logic (Security/Fact/Functionality rules).
    *   Create Markdown serialization logic for the `AuditReport`.
    *   Add conditional edges for error handling and recovery.

### **Day 6 (SATURDAY): MinMax Loop & Final Submission**
*   **Deadline:** 21:00 UTC
*   **Focus:** Validation & Reflection
*   **Key Tasks:**
    *   Run Self-Audit and fix repo gaps.
    *   Run Peer-Audit and deliver report.
    *   Record 5-min demo video and write final reflection.

---

## 3. Optimized AI Prompts (For Rovodev/Acli)

### **Sprint 1: The Interim Scaffold (WEDNESDAY)**
> "Act as a senior LangGraph developer. We need to build the infrastructure for the 'Automaton Auditor' project today. 
> 
> **Core Requirements:**
> 1. Setup a Python project using `uv`. Use `src/` layout.
> 2. Create `src/state.py`: Implement `Evidence` (Pydantic), `JudicialOpinion` (Pydantic), and `AgentState` (TypedDict). Use `operator.ior` for `evidences` dict and `operator.add` for `opinions` list to support parallel reduction.
> 3. Create `src/tools/repo_tools.py`: Implement a tool to clone a GitHub repo into a `tempfile.TemporaryDirectory`. Implement an AST-based function to check for `StateGraph` builder calls in a file.
> 4. Create `src/tools/doc_tools.py`: Implement PDF parsing using `docling` to extract text and images.
> 5. Create `src/graph.py`: Wire a `StateGraph` that starts, runs `RepoInvestigator` and `DocAnalyst` nodes in parallel, and finishes at an `EvidenceAggregator` node that prints the collected evidence.
> 
> **Constraints:** No Judicial nodes yet. Strict Pydantic typing. Clean error handling for git clone. No secrets in code."

### **Sprint 2: The Parallel Bench (THURSDAY)**
> "Act as an LLM Orchestration Expert. We are implementing the Judicial Layer.
> 
> **Core Requirements:**
> 1. In `src/nodes/judges.py`, implement three nodes: `Prosecutor`, `Defense`, and `TechLead`.
> 2. Use `.with_structured_output(JudicialOpinion)` for all three.
> 3. Give each judge a distinct system prompt:
>    - Prosecutor: Adversarial, focuses on gaps/security/laziness.
>    - Defense: Forgiving, focuses on intent/effort/creativity.
>    - Tech Lead: Pragmatic, focuses on debt/maintainability/viability.
> 4. Update `src/graph.py` to fan-out from `EvidenceAggregator` to these three nodes.
> 
> **Constraints:** Ensure the prompts prevent 'Persona Collusion'. The judges must analyze the *same* evidence but provide different scores and arguments."

### **Sprint 3: The Verdict & Reporting (FRIDAY)**
> "Act as a Senior Software Architect. We are building the Chief Justice synthesis node.
> 
> **Core Requirements:**
> 1. Implement `src/nodes/justice.py` with `ChiefJusticeNode`.
> 2. Implement deterministic Python rules: 
>    - 'Security Override': If a detective found a security flaw, max score is 3.
>    - 'Fact Supremacy': If a detective says a file is missing, ignore any judge claiming it exists.
>    - 'Variance Rule': If judge scores vary by > 2, add a 'Dissent Summary'.
> 3. Implement a function to serialize the final `AuditReport` Pydantic model into a clean Markdown file with sections for Summary, Criteria, and Remediation.
> 4. Wire this as the final node in `src/graph.py`.
> 
> **Constraints:** No LLM-based averaging for scores; use code logic for the verdict."

---

## 4. Submission Checklist (Fast Workflow)
- [ ] `pyproject.toml` (Managed by `uv`)
- [ ] `src/state.py` (Typed state with reducers)
- [ ] `src/tools/` (Forensic AST & PDF tools)
- [ ] `src/nodes/` (Detective, Judge, and Justice nodes)
- [ ] `src/graph.py` (Parallel Fan-Out/Fan-In logic)
- [ ] `reports/interim_report.pdf` (Architecture diagram + strategy)
- [ ] `.env.example` (API keys: Google/OpenAI, LangSmith)
