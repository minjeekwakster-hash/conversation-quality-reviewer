# Dashboard Redesign — Wireframes

**Primary Persona**: Sarah, QA Manager at JetBlue
- Reviews agent conversation quality daily
- Currently samples 1-3% of conversations manually
- Reports quality trends to VP of Customer Experience weekly
- Coaches agents based on quality findings
- Needs to know: "Are we meeting our quality bar? Where are the problems? What specifically went wrong?"

**Design Principles** (borrowed from Minji's voice-agent-ops + Mudflap dashboard):
- Status tables over charts — scannable, not decorative
- Hard blocks vs. warnings — not all failures are equal
- Progressive disclosure — overview → flow → conversation → turn
- Every number should answer a question Sarah is actually asking

---

## Navigation

Three tabs, named for what Sarah is trying to do (not what the tab contains):

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Quality Summary │  │  Review Queue    │  │  Conversation    │
│                  │  │                  │  │  Detail          │
└─────────────────┘  └─────────────────┘  └─────────────────┘
  "How are we        "Which calls need    "What happened
   doing?"            my attention?"       in this call?"
```

---

## View 1: Quality Summary ("How are we doing?")

What Sarah sees first thing Monday morning. Answers: "Are we above bar?"

```
┌──────────────────────────────────────────────────────────────────────┐
│  QUALITY SUMMARY                                    Last 24h ▼      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   78%    │  │   94%    │  │  12      │  │  226     │            │
│  │ Overall  │  │ Pass     │  │ Hard     │  │ Needs    │            │
│  │ Quality  │  │ Rate     │  │ Blocks   │  │ Review   │            │
│  │ 🟡 AT BAR│  │ 🟢 ABOVE │  │ 🔴 ACTION│  │          │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│                                                                      │
│  ── Quality Bar Definition ──────────────────────────────────────    │
│  🟢 Above Bar (≥0.80)  🟡 Marginal (0.50-0.79)  🔴 Below Bar (<0.50) │
│  Hard Block = Resolution failure OR Compliance violation             │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  QUALITY BY FLOW                                                     │
│  ┌───────────────────┬────────┬────────┬────────┬────────┬────────┐ │
│  │ Flow              │Overall │Resolve │Comply  │Effic.  │Status  │ │
│  ├───────────────────┼────────┼────────┼────────┼────────┼────────┤ │
│  │ Account Access     │ 0.88  │ 0.92  │ 0.90  │ 0.95  │ 🟢     │ │
│  │ Product Defect     │ 0.72  │ 0.65  │ 0.78  │ 0.91  │ 🟡     │ │
│  │ Purchase Dispute   │ 0.68  │ 0.60  │ 0.71  │ 0.88  │ 🟡     │ │
│  │ Troubleshoot Site  │ 0.45  │ 0.40  │ 0.38  │ 0.82  │ 🔴     │ │
│  │ ...                │       │       │       │       │        │ │
│  └───────────────────┴────────┴────────┴────────┴────────┴────────┘ │
│  Click a row to filter Review Queue by that flow →                   │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  SIGNAL BREAKDOWN                                                    │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  Resolution ████████████████░░░░  0.78  🟡  (weight: 30%)  │     │
│  │  Compliance █████████████████░░░  0.82  🟢  (weight: 25%)  │     │
│  │  Efficiency ███████████████████░  0.92  🟢  (weight: 15%)  │     │
│  │  Sentiment  ██████████████░░░░░░  0.71  🟡  (weight: 15%)  │     │
│  │  Communication ████████████████░░  0.79  🟡  (weight: 15%) │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌─────────────────────────────┐  ┌──────────────────────────────┐  │
│  │  RESOLUTION vs COMPLIANCE   │  │  SCORE DISTRIBUTION          │  │
│  │  (scatter plot)             │  │  (histogram)                 │  │
│  │                             │  │                              │  │
│  │     · ·  ·  │ · · ·  ·     │  │  ▓                           │  │
│  │   ·    ·    │  · · ·  · ·  │  │  ▓ ▓                         │  │
│  │  ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─  │  │  ▓ ▓ ▓                      │  │
│  │  ·  ·   ·  │    ·         │  │  ▓ ▓ ▓ ▓ ▓                   │  │
│  │    ·        │  ·           │  │  ▓ ▓ ▓ ▓ ▓ ▓ ▓               │  │
│  │  Compliance →              │  │  0.2  0.4  0.6  0.8  1.0     │  │
│  └─────────────────────────────┘  └──────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Key design choices**:
- KPI cards with tier status (🟢🟡🔴) — Sarah knows instantly if she needs to act
- "Hard Blocks" count is prominent — these are the fires to fight first
- Flow table is the centerpiece — scannable, sortable, clickable
- Charts are secondary (below the fold), not primary
- Quality bar definition is always visible — shared language with her VP

---

## View 2: Review Queue ("Which calls need my attention?")

Sarah's daily workflow. Sorted by severity. She picks conversations to review.

```
┌──────────────────────────────────────────────────────────────────────┐
│  REVIEW QUEUE                                 Filter: All Flows ▼   │
│                                               Showing: Flagged first│
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────┬────────┬──────────────────┬───────┬───────────────┬────────┐│
│  │ ID │ Flow   │ Issue            │Overall│ Flags         │ Action ││
│  ├────┼────────┼──────────────────┼───────┼───────────────┼────────┤│
│  │576 │Account │Compliance        │ 0.38  │🔴 HARD BLOCK  │ Review ││
│  │    │Access  │violation:        │       │Missing: verify│        ││
│  │    │        │identity not      │       │-identity      │        ││
│  │    │        │verified          │       │               │        ││
│  ├────┼────────┼──────────────────┼───────┼───────────────┼────────┤│
│  │382 │Trouble │Resolution failed:│ 0.39  │🔴 HARD BLOCK  │ Review ││
│  │    │shoot   │customer issue    │       │🔴 Low resolve │        ││
│  │    │        │unresolved        │       │               │        ││
│  ├────┼────────┼──────────────────┼───────┼───────────────┼────────┤│
│  │2901│Product │Sentiment drop:   │ 0.52  │⚠️ WARNING     │ Review ││
│  │    │Defect  │customer went from│       │Sentiment      │        ││
│  │    │        │positive to angry │       │deterioration  │        ││
│  ├────┼────────┼──────────────────┼───────┼───────────────┼────────┤│
│  │4410│Order   │Communication:    │ 0.61  │⚠️ WARNING     │ Review ││
│  │    │Issue   │low empathy (0.35)│       │Flagged        │        ││
│  │    │        │during complaint  │       │utterances     │        ││
│  └────┴────────┴──────────────────┴───────┴───────────────┴────────┘│
│                                                                      │
│  ── Summary ─────────────────────────────────────────────────────    │
│  🔴 12 Hard Blocks (must review)                                     │
│  ⚠️ 214 Warnings (review recommended)                               │
│  🟢 7,808 Passing (no action needed)                                 │
│                                                                      │
│  Click "Review" to open Conversation Detail →                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Key design choices**:
- Hard blocks sort to the top — most urgent first
- "Issue" column explains WHY it's flagged in plain English, not just a score
- Each row has enough context to decide whether to click into detail
- Summary bar at bottom gives the full picture (12 fires / 214 concerns / 7808 fine)

---

## View 3: Conversation Detail ("What happened in this call?")

Sarah clicked into conversation #576. She needs to understand what went
wrong and decide on coaching action.

```
┌──────────────────────────────────────────────────────────────────────┐
│  CONVERSATION #576                                    ← Back to Queue│
│  Account Access / Status Shipping Question                           │
│  Customer: bronze member                                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐      │
│  │  OVERALL: 0.38  🔴 BELOW BAR                              │      │
│  │  Hard Block: Compliance violation — identity not verified  │      │
│  └────────────────────────────────────────────────────────────┘      │
│                                                                      │
│  ── Score Card ──────────────────────────────────────────────────    │
│                                                                      │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐    │
│  │   Radar Chart    │    │  Signal       Score  Status          │    │
│  │                  │    │  ─────────────────────────────────── │    │
│  │    Resolve       │    │  Resolution    0.45  🔴 Hard Block   │    │
│  │   /    \         │    │  Compliance    0.22  🔴 Hard Block   │    │
│  │ Comm    Comply   │    │  Efficiency    0.85  🟢 Above Bar    │    │
│  │   \    /         │    │  Sentiment     0.55  🟡 Marginal     │    │
│  │  Sent──Effic     │    │  Communication 0.48  🟡 Marginal     │    │
│  │                  │    │                                      │    │
│  └─────────────────┘    └──────────────────────────────────────┘    │
│                                                                      │
│  ── What Went Wrong ────────────────────────────────────────────    │
│  🔴 Agent never verified customer identity (required for account     │
│     access flows). Expected action: verify-identity. Not performed.  │
│  🔴 Customer's shipping question was not fully resolved — agent      │
│     provided partial information but did not confirm resolution.     │
│  ⚠️ Empathy score low (0.35) — agent did not acknowledge            │
│     customer's frustration about delayed shipment.                   │
│                                                                      │
│  ── What Went Well ─────────────────────────────────────────────    │
│  🟢 Efficient conversation — 18 turns vs. 22 avg for this flow      │
│  🟢 Clear communication — agent explained shipping status clearly    │
│  🟢 Correct action sequence (except missing verify-identity)         │
│                                                                      │
│  ── Compliance Detail ──────────────────────────────────────────    │
│  Expected: pull-up-account → ask-the-oracle → send-link             │
│  Actual:   pull-up-account → ask-the-oracle                         │
│  Missing:  verify-identity, send-link                                │
│  LLM adjustment: -0.05 (agent skipped identity check without        │
│  justification — customer did not proactively provide credentials)   │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ── Sentiment Trajectory ───────────────────────────────────────    │
│                                                                      │
│   1.0 ┤                                                              │
│   0.5 ┤──●                                                           │
│   0.0 ┤     ●──●                                                     │
│  -0.5 ┤           ●──●                                               │
│  -1.0 ┤                 ●                                            │
│       └──────────────────── turns →                                  │
│   ▲ Frustration spike at turn 8 (shipping delay mentioned)           │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ── Transcript ─────────────────────────────────────────────────    │
│                                                                      │
│  🟦 AGENT: Hi! How can I help you?                                   │
│  🟩 CUSTOMER: Hi, I need to check on my shipping status (😐 0.2)    │
│  🟦 AGENT: Sure, let me pull up your account.                        │
│  ⚙️ ACTION: Account pulled up for John Smith                        │
│  🟩 CUSTOMER: I ordered 3 days ago and still no update (😠 -0.3)    │
│  🟦 AGENT: I see your order here. Let me check.                     │
│     ⚠️ LOW EMPATHY — did not acknowledge frustration                 │
│  ⚙️ ACTION: ask-the-oracle                                          │
│  🟦 AGENT: Your order is in processing.                              │
│  🟩 CUSTOMER: That's not helpful, when will it ship? (😡 -0.6)      │
│     ▲ FRUSTRATION SPIKE                                              │
│  ...                                                                 │
│  ❌ MISSING: verify-identity (never performed)                       │
│  ❌ MISSING: send-link (never performed)                             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Key design choices**:
- Hard block banner at top — Sarah knows immediately this is a serious issue
- "What Went Wrong / What Went Well" in plain English — not just scores
- Compliance detail shows expected vs. actual action sequence visually
- Transcript has inline annotations: sentiment scores, empathy flags, missing actions
- Sentiment chart shows the trajectory with spike markers
- Everything Sarah needs to write a coaching note is on one screen

---

## Signal Definitions (shown in sidebar or tooltip)

These are the shared quality definitions Sarah and her VP align on:

| Signal | What It Measures | Hard Block? | Above Bar | Marginal | Below Bar |
|--------|-----------------|-------------|-----------|----------|-----------|
| Resolution | Did the agent solve the customer's issue? | Yes (if <0.50) | ≥0.80 | 0.50-0.79 | <0.50 |
| Compliance | Did the agent follow the required procedure? | Yes (if <0.50) | ≥0.80 | 0.50-0.79 | <0.50 |
| Efficiency | Was the conversation handled efficiently? | No | ≥0.80 | 0.50-0.79 | <0.50 |
| Sentiment | Did customer sentiment stay positive/recover? | No | ≥0.80 | 0.50-0.79 | <0.50 |
| Communication | Was the agent clear, empathetic, professional? | No | ≥0.80 | 0.50-0.79 | <0.50 |

**Hard Block rule**: Resolution < 0.50 OR Compliance < 0.50 = hard block.
These conversations MUST be reviewed. All others are warnings or passing.

---

## Changes from Current Dashboard

| Current | Redesigned | Why |
|---------|-----------|-----|
| Tab names: "Overview", "Deep Dive", "Comparison" | "Quality Summary", "Review Queue", "Conversation Detail" | Named for what Sarah is trying to DO, not what the tab contains |
| Histogram-first layout | Status table first, charts secondary | QA managers scan tables, not charts |
| No quality bar definition | 🟢🟡🔴 tier bars always visible | Shared language with VP — "are we above bar?" |
| No hard blocks concept | Hard blocks sort to top of queue | Not all failures are equal — some need immediate action |
| Scores only | "What Went Wrong / What Went Well" sections | Plain English > numbers for coaching conversations |
| Comparison view (high vs. low) | Removed — replaced with Review Queue | Sarah doesn't compare random pairs; she triages a queue |
| Generic scatter plot | Scatter plot with quadrant labels stays | "Cowboy vs. by-the-book" insight is genuinely useful |
