# Enhanced Architecture Diagram Specification

## Goal: Achieve 30/30 on "Architecture Deep Dive and Diagrams"

**Current Score:** 28/30  
**Gap:** Missing explicit labels for fan-out/fan-in patterns and conditional error edges  
**Target:** Add visual clarity to achieve perfect score

---

## Required Enhancements (Per Rubric Feedback)

### 1. **Explicit Fan-Out/Fan-In Labels**

**Add these text labels directly on the diagram:**

**Fan-Out #1 (Detective Layer):**
```
┌─────────────────────────────────────────────────┐
│   FAN-OUT #1: PARALLEL DETECTIVE EXECUTION      │
│   (Concurrent Evidence Collection)               │
└─────────────────────────────────────────────────┘
         ↓                ↓                ↓
  RepoInvestigator  DocAnalyst    VisionInspector
```

**Fan-In #1 (Evidence Aggregation):**
```
  RepoInvestigator  DocAnalyst    VisionInspector
         ↓                ↓                ↓
┌─────────────────────────────────────────────────┐
│   FAN-IN #1: EVIDENCE SYNCHRONIZATION           │
│   (Waits for all 3 detectives to complete)      │
└─────────────────────────────────────────────────┘
                      ↓
              EvidenceAggregator
```

**Fan-Out #2 (Judicial Layer):**
```
┌─────────────────────────────────────────────────┐
│   FAN-OUT #2: PARALLEL JUDICIAL DELIBERATION    │
│   (Adversarial Multi-Perspective Evaluation)    │
└─────────────────────────────────────────────────┘
         ↓                ↓                ↓
    Prosecutor        Defense         TechLead
```

**Fan-In #2 (Synthesis):**
```
    Prosecutor        Defense         TechLead
         ↓                ↓                ↓
┌─────────────────────────────────────────────────┐
│   FAN-IN #2: DETERMINISTIC SYNTHESIS            │
│   (Waits for all 3 judges, applies rules)       │
└─────────────────────────────────────────────────┘
                      ↓
               ChiefJustice
```

---

### 2. **Conditional Error Edges**

**Add these dashed/colored edges with labels:**

**From RepoInvestigator:**
```
RepoInvestigator ┄┄┄┄┄┄┄┄> EvidenceAggregator
                 (if clone fails: skip repo evidence)
```

**From DocAnalyst:**
```
DocAnalyst ┄┄┄┄┄┄┄┄> EvidenceAggregator
           (if PDF missing: skip doc evidence)
```

**From VisionInspector:**
```
VisionInspector ┄┄┄┄┄┄┄┄> EvidenceAggregator
                (if no images: skip vision evidence)
```

**From Judges:**
```
Prosecutor ┄┄┄┄┄┄┄┄> ChiefJustice
           (if malformed output: retry 3x → fallback)
```

---

### 3. **Color Coding (Recommended)**

**Layer Colors:**
- **Blue Background:** Detective Layer (RepoInvestigator, DocAnalyst, VisionInspector)
- **Red Background:** Judicial Layer (Prosecutor, Defense, TechLead)
- **Green Background:** Synthesis Layer (ChiefJustice)
- **Gray Background:** Infrastructure (ContextBuilder, EvidenceAggregator)

**Edge Colors:**
- **Solid Black:** Happy path (successful execution)
- **Dashed Red:** Error handling (conditional recovery)
- **Bold Blue:** Synchronization edges (fan-in points)

---

### 4. **Legend (Must Include)**

```
┌─────────────────────────────────────────────────┐
│ LEGEND                                           │
├─────────────────────────────────────────────────┤
│ ━━━  Solid line: Happy path execution          │
│ ┄┄┄  Dashed line: Error handling / Conditional │
│ ━━━> Bold arrow: Synchronization (fan-in)      │
│  ◆   Diamond: Synchronization point (waits)    │
│  ▶   Triangle: Fan-out point (spawns parallel) │
│                                                  │
│ COLORS:                                          │
│ 🔵 Blue: Detective Layer                        │
│ 🔴 Red: Judicial Layer                          │
│ 🟢 Green: Synthesis Layer                       │
│ ⚫ Gray: Infrastructure                          │
└─────────────────────────────────────────────────┘
```

---

### 5. **Node Annotations**

**Add small text under each node:**

**ContextBuilder:**
```
┌──────────────────┐
│ ContextBuilder   │
├──────────────────┤
│ Initialize state │
│ Load rubric      │
└──────────────────┘
```

**EvidenceAggregator:**
```
┌──────────────────────┐
│ EvidenceAggregator   │
├──────────────────────┤
│ ◆ SYNC POINT         │
│ Merge detective data │
│ Cross-reference PDF  │
└──────────────────────┘
```

**ChiefJustice:**
```
┌──────────────────────┐
│ ChiefJustice         │
├──────────────────────┤
│ ◆ SYNC POINT         │
│ Apply deterministic  │
│ conflict rules       │
└──────────────────────┘
```

---

## Complete Enhanced Diagram Layout

```
                           ┌─────────┐
                           │  START  │
                           └────┬────┘
                                │
                         ┌──────▼──────┐
                         │Context      │
                         │Builder      │
                         │(Initialize) │
                         └──────┬──────┘
                                │
         ┌──────────────────────┴──────────────────────┐
         │  FAN-OUT #1: PARALLEL DETECTIVE EXECUTION   │
         │  ▶ (Concurrent Evidence Collection)         │
         └──────────────────────┬──────────────────────┘
                 ┌──────────────┼──────────────┐
                 │              │              │
        ┌────────▼────────┐ ┌──▼────┐ ┌───────▼────────┐
        │🔵 Repo         │ │🔵 Doc  │ │🔵 Vision       │
        │Investigator    │ │Analyst │ │Inspector       │
        │(AST,git,files) │ │(PDF)   │ │(Images)        │
        └────────┬────────┘ └──┬────┘ └───────┬────────┘
                 │ ━━━━━━━━━━━━│━━━━━━━━━━━━━━│
                 │ ┄┄┄ error ┄┄│┄┄ handlers ┄┄│┄┄┄
                 │              │              │
         ┌───────┴──────────────┴──────────────┴───────┐
         │  FAN-IN #1: EVIDENCE SYNCHRONIZATION        │
         │  ◆ (Waits for all 3 detectives)             │
         └───────────────────┬─────────────────────────┘
                      ┌──────▼──────┐
                      │⚫ Evidence   │
                      │Aggregator   │
                      │(Merge+Xref) │
                      └──────┬──────┘
                             │
         ┌───────────────────┴────────────────────┐
         │  FAN-OUT #2: PARALLEL JUDICIAL         │
         │  ▶ (Adversarial Multi-Perspective)     │
         └───────────────────┬────────────────────┘
                 ┌───────────┼───────────┐
                 │           │           │
        ┌────────▼────┐ ┌────▼─────┐ ┌──▼────────┐
        │🔴 Prosecutor│ │🔴 Defense│ │🔴 TechLead│
        │(Adversarial)│ │(Optimist)│ │(Architect)│
        └────────┬────┘ └────┬─────┘ └──┬────────┘
                 │ ━━━━━━━━━━│━━━━━━━━━━│
                 │ ┄┄┄ retry ┄│┄ logic ┄┄│┄┄┄
                 │            │          │
         ┌───────┴────────────┴──────────┴───────┐
         │  FAN-IN #2: DETERMINISTIC SYNTHESIS   │
         │  ◆ (Waits for all 3, applies rules)   │
         └───────────────────┬───────────────────┘
                      ┌──────▼──────┐
                      │🟢 Chief     │
                      │Justice      │
                      │(Governance) │
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │   END       │
                      │(Report out) │
                      └─────────────┘
```

---

## Implementation Options

### Option 1: Create New Diagram with Tool

**Recommended Tools:**
1. **Draw.io (diagrams.net)** - Free, web-based
   - Go to: https://app.diagrams.net/
   - Import existing diagram or start fresh
   - Add text boxes for labels
   - Use color fill for layer backgrounds
   - Export as PNG

2. **Mermaid** - Code-based diagrams
   - Edit markdown with Mermaid syntax
   - Render to PNG via mermaid.live
   - Embed in report

3. **Excalidraw** - Hand-drawn style
   - Go to: https://excalidraw.com/
   - Quick sketching with labels
   - Export as PNG

### Option 2: Annotate Existing Diagram

**If you have image editing software:**
1. Open `reports/stategraph_architecture.png` in tool (Paint, GIMP, Photoshop)
2. Add text boxes with labels as specified above
3. Add colored rectangles behind layers
4. Add legend box in corner
5. Save as new version

### Option 3: Generate Programmatically

**Using Python + Graphviz:**
```python
from graphviz import Digraph

dot = Digraph(comment='Digital Courtroom Architecture')
dot.attr(rankdir='TB', bgcolor='white')

# Add nodes with colors and labels
# Add edges with styles
# Render to PNG
```

---

## Timeline

**Estimated Time:** 30-45 minutes
- Choose tool: 5 min
- Create diagram: 20-30 min
- Export and verify: 5 min
- Update report: 5 min
- Commit and push: 5 min

---

## Expected Outcome

**Before:** 28/30 (missing explicit labels)  
**After:** 30/30 (all rubric criteria met)

**Rubric Alignment:**
✅ "Visually distinct parallel branches for both Detectives and Judges"  
✅ "Fan-in synchronization points"  
✅ "Synthesis endpoint"  
✅ Explicit labels for patterns  
✅ Conditional error edges shown

**Total Report Score:** 98/100 → 100/100 (+2 pts)
