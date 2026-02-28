# Demo Video Script (5 Minutes Max)

## Target: 20/20 Points on Demo Video Rubric

### Rubric Breakdown:
1. **End-to-End Pipeline Execution** (5 pts) - Live run with real inputs
2. **Layered Architecture Visibility** (5 pts) - Show all 3 layers distinctly
3. **Concept Translation & Strategic Justification** (5 pts) - Explain the "why"
4. **Professional Delivery & Pacing** (5 pts) - Within 5 minutes, clear structure

---

## Script Timeline (Total: 4:45)

### [0:00-0:30] Introduction & Context (30 seconds)
**Show:** Title slide or README
**Say:**
> "This is the Automaton Auditor - a multi-agent system that audits AI-generated codebases using a Digital Courtroom architecture. Instead of a single AI grading another AI's work, we use three conflicting judge personas debating the same forensic evidence, then resolve their disagreements deterministically."

**Why this works:** Immediately establishes strategic purpose (autonomous governance at scale)

---

### [0:30-1:00] Architecture Overview (30 seconds)
**Show:** `reports/stategraph_architecture.png`
**Say:**
> "The system has three layers: Detective agents run in parallel collecting structured evidence using AST parsing and PDF cross-referencing. Then three Judge personas - Prosecutor, Defense, and Tech Lead - evaluate that same evidence with genuinely conflicting philosophies. Finally, a Chief Justice applies deterministic rules to resolve conflicts without LLM averaging."

**Point to diagram:** Show the two fan-out/fan-in patterns

**Why this works:** Covers Fan-In/Fan-Out and Dialectical Synthesis concepts

---

### [1:00-3:30] Live Execution (2:30 minutes)
**Show:** Terminal running the audit
**Commands:**
```bash
# Show the inputs
ls reports/final_report.pdf
cat .env | grep LANGCHAIN_TRACING

# Run the audit
python -m src.graph \
  --repo https://github.com/78gk/The-Automaton-Auditor \
  --pdf reports/final_report.pdf \
  --output audit/demo_run
```

**During execution, narrate:**

**[1:00-1:30] Detective Layer**
> "Watch the three detectives run in parallel. RepoInvestigator is cloning the repo and parsing the StateGraph AST. DocAnalyst is chunking the PDF. VisionInspector is extracting diagrams."

**Show:** Console logs showing parallel execution, then Evidence objects

**[1:30-2:15] Judicial Layer**
> "Now the three judges receive the same evidence but argue from different perspectives. The Prosecutor is adversarial, looking for security flaws and gaps. The Defense rewards effort and intent. The Tech Lead focuses on architectural soundness."

**Show:** Console logs showing JudicialOpinion objects with different scores

**Point out:** "Notice they disagree - the Prosecutor gave a 2, the Defense gave a 4 for the same criterion."

**[2:15-3:00] Chief Justice Synthesis**
> "The Chief Justice doesn't use another LLM to average scores. Instead, deterministic Python rules apply: security flaws cap scores, detective facts override unsupported judge claims, and the Tech Lead opinion carries more weight for architecture decisions."

**Show:** Console logs showing conflict resolution and final scores

**[3:00-3:30] Final Output**
> "The output is a complete Markdown audit report with executive summary, per-criterion breakdown showing all three judge opinions, dissent summaries where disagreement exceeded 2 points, and a remediation plan with file-level instructions."

**Show:** Open `audit/demo_run/audit_report.md` briefly

---

### [3:30-4:15] Strategic Justification (45 seconds)
**Show:** Back to diagram or code
**Say:**
> "Why this architecture? First, parallel fan-out reduces latency - all detectives run simultaneously. Second, dialectical synthesis prevents persona collusion - if judges agree too easily, we're not stress-testing the evaluation. Third, deterministic conflict resolution ensures facts dominate persuasion - an adversarial judge can't talk their way around missing evidence."

**Why this works:** Explains 2+ architectural choices with business justification

---

### [4:15-4:45] LangSmith Trace & Wrap (30 seconds)
**Show:** LangSmith dashboard with trace
**Say:**
> "The entire execution is traced in LangSmith. You can see every node, every LLM call, and verify that the pipeline completed end-to-end with no failures. This is critical for debugging multi-agent systems at scale."

**Show:** Click through trace tree showing all layers

**Close:**
> "This demonstrates autonomous quality assurance - a system that can evaluate AI-generated code with forensic rigor, conflicting perspectives, and deterministic governance."

---

## Recording Setup

### Before Recording:
1. ✅ Close all unnecessary apps
2. ✅ Clear terminal history
3. ✅ Have LangSmith trace open in browser tab
4. ✅ Test full run to ensure no errors
5. ✅ Prepare screen layout (terminal + browser side-by-side)

### Recording Tools:
- **Windows:** OBS Studio or Xbox Game Bar (Win+G)
- **Mac:** QuickTime or Screen Studio
- **Settings:** 1080p minimum, clear audio

### Delivery Tips:
- Speak clearly and confidently
- No filler words ("um", "like", "so")
- Point with cursor to highlight key areas
- Stay under 5 minutes (4:45 target leaves buffer)

---

## Rubric Alignment Checklist

**End-to-End Pipeline Execution (5 pts):**
- ✅ Real repo URL and PDF as inputs
- ✅ Pipeline runs to completion on screen
- ✅ Final Markdown report shown
- ✅ Clearly not mocked or pre-recorded

**Layered Architecture Visibility (5 pts):**
- ✅ Detective Evidence objects visible
- ✅ Judge opinions show conflicting scores
- ✅ Chief Justice references disagreement
- ✅ Can trace data flow layer to layer

**Concept Translation (5 pts):**
- ✅ Explain why parallel fan-out
- ✅ Explain why three personas vs one grader
- ✅ Explain why deterministic rules
- ✅ Connect to autonomous governance at scale

**Professional Delivery (5 pts):**
- ✅ Under 5 minutes
- ✅ Clear structure (intro → architecture → execution → justification → close)
- ✅ No rambling or dead time
- ✅ Good audio/video quality

---

## After Recording:
1. Upload to YouTube/Vimeo/Google Drive (set to unlisted or public)
2. Add link to submission
3. Test playback to verify quality
