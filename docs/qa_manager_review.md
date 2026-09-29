# QA Manager Dashboard Review
**Persona**: Sarah Chen, QA Manager — JetBlue Contact Center
**Context**: Manages a team of 12 QA analysts covering ~3,000 customer interactions/day across chat and voice. Currently samples 1-5% of interactions manually.

---

## My Top 3 Critical Workflows

### Workflow 1: Morning Triage — "What broke overnight?"
**Frequency**: Daily (first thing every morning, 7:30 AM)
**Pain Level**: 🔴 Extreme

Every morning I open my dashboard and need to answer one question in under 30 seconds: **"Is anything on fire?"** Did we have a compliance failure that Legal needs to know about? Did a new product launch cause a spike in unresolved issues? Is a specific call reason tanking?

This is the workflow that keeps me employed. If a compliance failure slips through and becomes a regulatory finding, that's a career-ending event. If resolution rates on refunds dropped 15% overnight because of a policy change nobody told us about, I need to know before my VP does.

**What I actually do**:
1. Glance at top-line numbers (pass rate, hard blocks, overall quality)
2. Compare to yesterday — are we trending up or down?
3. Spot any new clusters of failures (by call reason)
4. Identify anything that needs immediate escalation
5. Decide: "Normal day" vs. "All-hands" vs. "Escalate to VP"

---

### Workflow 2: Coaching Prep — "Who do I coach and on what?"
**Frequency**: 3x/week (prep for coaching sessions with agents)
**Pain Level**: 🟡 High

I sit down with 3-4 agents per week for 1:1 coaching. The worst thing I can do is show up with vague feedback ("Your scores are low"). I need **specific conversations with specific moments** — "On this call at 2:47pm, the customer said X and you responded with Y. Here's why that's a problem and what to say instead."

Today I pull random samples. I might review 10 calls and find nothing coachable, or I might find an issue but it's from 3 weeks ago and the agent doesn't remember it. The tool needs to surface the right conversations fast and give me the evidence I need to make coaching stick.

**What I actually do**:
1. Pull up an agent's recent interactions (we don't have agent IDs in this dataset — noted)
2. Find 2-3 conversations with clear coaching moments
3. Identify the specific failure pattern (empathy? compliance? clarity?)
4. Prepare "What happened → Why it matters → What to do instead"
5. Build a coaching narrative across the conversations (is this a pattern or a one-off?)

---

### Workflow 3: Weekly Reporting — "What's the story this week?"
**Frequency**: Weekly (Friday afternoon for Monday leadership meeting)
**Pain Level**: 🟡 Moderate

Every Monday I present to the Director of Customer Service. They don't want raw numbers — they want the narrative. "Refund-related calls are improving because we retrained on the new policy last week." "Troubleshooting calls are getting worse because the new website update is confusing customers." I need to connect quality signals to business causes and prove that my coaching interventions are working.

**What I actually do**:
1. Pull aggregate metrics by call reason
2. Compare week-over-week trends
3. Identify top 2-3 quality stories (improvements and regressions)
4. Correlate with known business events (product launches, policy changes, staffing)
5. Prepare 3-5 slide deck with data + recommendations

---

## Dashboard Assessment by Workflow

---

## Workflow 1: Morning Triage — "What broke overnight?"

### What's Great

**The 4 KPI cards nail the "5-second scan."** Overall Quality, Pass Rate, Hard Blocks, and Needs Review — these are exactly the four numbers I want to see first. Hard Blocks as a standalone count is smart; it forces my eye there immediately. If that number is anything other than zero, I'm already in action mode.

**The alert banner is exactly right.** When hard blocks exist, the system actively tells me "Go to Review Queue." Don't make me figure out what to do — tell me. That's good UX for someone who's already stressed at 7:30 AM.

**The Call Reason breakdown table is the core of triage.** Being able to sort by "Hard Blocks" or "Flagged %" means I can instantly see which call reasons are driving problems. The "Biggest Gap" column is clever — instead of making me scan 5 signal columns, you tell me the one thing that's dragging each call reason down. That's how I think: "What's the single biggest issue with refund calls right now?"

**The tiered color system (🟢🟡🔴) is intuitive and doesn't require training.** My analysts can read this on day one.

**Hard block gating logic is sound.** Resolution < 0.50 OR Compliance < 0.50 triggering mandatory review — yes, these are the two non-negotiable signals. An efficient, well-communicated call that didn't resolve the issue or violated policy is still a failure. Good product judgment here.

### What's Missing / Gaps

**No time dimension — this is the single biggest gap in the entire dashboard.** I can see where I am today, but I cannot see if it's better or worse than yesterday, last week, or last month. Without trends, every morning looks like a snapshot with no context. Here's what happens without trends:
- I see 12 hard blocks. Is that normal? Is that a spike? I genuinely don't know.
- I see refund quality at 0.68. Was it 0.72 last week? 0.55? Without the delta, I can't prioritize.
- My VP asks "Is quality improving?" and I have no answer.
- I can't prove my coaching interventions are working.

This isn't a "nice to have" — it's the difference between reactive firefighting and proactive quality management. A simple sparkline or delta indicator (↑3% vs last week) next to each KPI would transform this view.

**No time-based filtering.** I can filter by call reason but not by date range. "Show me last night's conversations" vs. "show me last week" — I need both. Morning triage is about the last 12-24 hours. Weekly reporting is about the last 7 days. These are fundamentally different time slices.

**No severity/urgency ranking within hard blocks.** If I have 12 hard blocks, which ones are the most severe? A compliance failure on a payment call is orders of magnitude more serious than a resolution failure on a "check order status" call. The dashboard treats all hard blocks equally, but they're not. Some combination of: call reason sensitivity, customer tier (member level), and how far below threshold the score fell would help me triage within the red zone.

**No notification or alert threshold configuration.** In production, I'd want to set: "Alert me on Slack if hard blocks exceed 5 in any 4-hour window" or "Flag if any call reason's compliance drops below 0.60." The dashboard is passive — I have to come look at it. The best monitoring tools come find me.

### What I'd Deem Unnecessary

**The Coaching Pattern Map (scatter plot) in the Quality Summary view feels misplaced for morning triage.** It's a coaching tool, not a triage tool. At 7:30 AM, I'm not thinking about coaching quadrants — I'm thinking about "what needs escalation right now." The scatter plot is interesting but its placement in the summary view implies it's a daily-use artifact. I'd use it maybe once a week when prepping coaching themes.

**The Score Distribution histogram is analytically interesting but not actionable for triage.** Knowing that 23% of conversations fell in the 0.6-0.7 bucket doesn't tell me what to do. It's a "so what?" chart. The information it conveys (how many are passing/marginal/failing) is already in the KPI cards. The histogram would be more useful in a weekly/monthly analytics view where I'm looking at distribution shape changes over time.

**The expandable Signal Breakdown per call reason is too much detail for triage.** I just need the "Biggest Gap" column (which you already have — good). The expandable section with all 5 signals per call reason is what I'd use in a deep-dive, not in morning triage. It slows down my scan.

---

## Workflow 2: Coaching Prep — "Who do I coach and on what?"

### What's Great

**The Review Queue with priority sorting is exactly how I'd work.** Hard blocks first, then warnings. This is how I triage my coaching inbox. I don't want to wade through passing conversations to find the bad ones.

**The conversation detail view is outstanding — this is the best part of the entire dashboard.** Specifically:

- **Key Insights (TL;DR)** is gold for coaching. It gives me the "here's what happened" narrative in 3-5 bullet points, prioritized by severity. I can read this aloud in a coaching session: "Here's what the system flagged..."
- **What Went Wrong / What Went Well** in two columns is exactly the coaching frame. I always want to lead with a strength before discussing the gap. The fact that the dashboard structures it this way shows product empathy.
- **Flagged utterances highlighted in the transcript** — this is the "rewind to 2:47" moment. Instead of reading the entire 30-turn transcript, I can jump directly to the problem moments. The red highlighting on agent turns with issues is a massive time saver.
- **Sentiment trajectory chart** is a powerful coaching artifact. Being able to show an agent "See this — the customer's frustration spiked here, and you responded with [quote]" is concrete feedback that drives behavior change.
- **Compliance Detail with expected vs. actual action sequence** — the checkmarks (✅/❌) make it trivially easy to see what steps were missed. I can point at this and say "You skipped identity verification before processing the refund. Here's why that matters."
- **The radar chart** gives a quick shape-of-performance view. In coaching I'd say: "Your empathy and resolution are strong, but see how compliance dips? That's our focus area."
- **Communication sub-scores** (clarity, empathy, professionalism, proactiveness) break an abstract concept into coachable dimensions. "Empathy" is vague; "empathy: 0.45" with evidence quotes is specific.

**The "Add Feedback" button placeholder is the right signal.** Even disabled, it tells evaluators "we thought about the human-in-the-loop" and it shows me (the QA manager) where my coaching notes would go. Smart product decision to include it as a disabled feature with help text rather than omitting it entirely.

### What's Missing / Gaps

**No agent-level aggregation.** This is acknowledged in the scope guardrails (ABCD dataset lacks agent IDs), but it's worth calling out as the #1 gap for coaching. In my real workflow, I don't coach conversations — I coach agents. I need to see: "Agent Jessica has had 4 compliance flags this week across different call types. This is a pattern, not a bad day." Without agent-level views, every conversation is an isolated incident, and I can't distinguish a systemic agent skill gap from a one-off mistake. For the presentation, I'd talk about how agent-level aggregation enables:
  - Pattern detection across an agent's recent history
  - Coaching priority scores (which agent needs coaching most urgently?)
  - Before/after tracking (did coaching on compliance actually improve Jessica's scores?)

**No way to group or tag conversations for a coaching session.** When I'm prepping for a 1:1, I want to bookmark 3-4 conversations, add my notes to each, and pull them up in sequence during the coaching meeting. Currently the Review Queue is a flat list — I can review one conversation at a time but can't curate a coaching "packet." Something as simple as a "Save for coaching" button that builds a session list would be transformative.

**No comparative view between conversations.** When coaching, I often want to show: "Here's a call you handled poorly, and here's a similar call (same call reason, same subflow) that another agent handled well." Side-by-side comparison is a powerful coaching technique. The dashboard only shows one conversation at a time.

**The coaching connection between Quality Summary and Review Queue is one-directional.** I can click "Review →" on a conversation, but I can't go from the Quality Summary's "Biggest Gap" insight directly to the relevant conversations. For example, if I see "Refund calls have low compliance," I want to click on that row and get filtered Review Queue showing specifically refund conversations with compliance failures. Currently I'd need to mentally note the issue, switch views, and set filters manually.

**No recommended coaching talking points.** The LLM that scored the conversation already understands what went wrong. It could generate: "Suggested coaching points: (1) Practice empathy acknowledgment before jumping to resolution. (2) Always verify customer identity before processing financial transactions." This turns the tool from "here's what's wrong" into "here's what to do about it."

### What I'd Deem Unnecessary

**The API Reference section in the sidebar is developer-facing, not QA-manager-facing.** I will never run a curl command. This should be in documentation or a developer portal, not taking up real estate in my daily tool. It signals "this was built by engineers for engineers" rather than "this was built for me."

**The direct Conversation ID lookup is a power-user feature that I'd rarely use.** In my workflow, conversations come to me through the priority queue, not by ID. The only time I'd search by ID is if an escalation email references a specific case number — and even then, I'd probably just Ctrl+F. The space this takes could be better used for filter controls or coaching tools.

---

## Workflow 3: Weekly Reporting — "What's the story this week?"

### What's Great

**The Quality by Call Reason table is the backbone of my weekly narrative.** When sorted by quality (low to high), I can immediately see which call reasons are underperforming. The "Biggest Gap" column helps me tell the story: "Refund calls are our weakest area, driven primarily by compliance gaps."

**The Signal Breakdown bar chart provides a clean system-level view.** For leadership, I can say: "Across all interactions this week, resolution is strong at 0.82 but compliance is marginal at 0.71 — here's what we're doing about it." The weights shown on each bar help me explain why overall quality is what it is.

**The Top Issues section (when filtered by call reason) gives me drill-down detail for my narrative.** "The top failure signal for refund calls is compliance, with 'verify identity' being the most commonly missed action." That's a specific, actionable finding I can put on a slide.

**The pass rate metric is a clean headline number for leadership.** "87% of interactions met our quality bar this week" is the kind of sentence my VP can repeat in their own meeting.

### What's Missing / Gaps

**No week-over-week comparison — this is a dealbreaker for weekly reporting.** My entire weekly report is about deltas: "Quality improved from 78% to 82%." "Hard blocks decreased from 15 to 8." "Refund compliance improved from 0.61 to 0.74 after Tuesday's retraining." Without temporal comparison, the dashboard gives me a snapshot but not a story. A story requires movement.

For the presentation, I'd frame this as:
- **Sprint 1**: Snapshot dashboard (what we built — current state view)
- **Sprint 2**: Trend lines and delta indicators (week-over-week, configurable windows)
- **Sprint 3**: Correlation with interventions (tag coaching sessions, policy changes; see impact)

**No export or report generation.** I need to put numbers into a slide deck or email. Currently I'd screenshot charts or manually transcribe numbers. Even a basic "Export Summary as PDF" or "Copy metrics to clipboard" would save me 20 minutes of report prep every Friday.

**No ability to annotate or explain data anomalies.** When compliance dipped on Wednesday because of a system outage (agents couldn't access the policy tool), I need to annotate that so leadership doesn't misinterpret the data. Without annotations, every dip looks like an agent performance problem. In reality, many quality fluctuations are caused by system issues, policy changes, or customer behavior shifts — not agent behavior.

**No volume context alongside quality.** Quality scores without volume are misleading. "Troubleshoot calls have 0.92 quality" sounds great until you learn there were only 3 of them. "Refund calls have 0.68 quality" sounds concerning but might be acceptable if there were 500 of them and they're inherently harder. The Call Reason table should show conversation count (N) alongside quality metrics. I see "Flagged: N/M (X%)" which partially addresses this, but the total count (M) should be more prominent, perhaps as its own column.

**No benchmark or target line.** The tier thresholds (🟢 ≥0.80, 🟡 0.50–0.79, 🔴 <0.50) are useful but generic. In practice, I'd have specific targets set with leadership: "Refund compliance target: 0.85 by Q3." "Overall quality target: 0.80." Without customizable targets, I can't report progress toward goals — only position relative to arbitrary thresholds.

### What I'd Deem Unnecessary

**The Coaching Pattern Map (scatter plot) adds no value for weekly reporting.** Leadership doesn't think in quadrants. They think in: "What improved, what got worse, why, and what are we doing about it?" The scatter plot is analytically sophisticated but communicatively opaque — it requires explanation every time. For a weekly report, simple trend lines and bar charts with deltas are far more effective.

**The Score Distribution histogram, again, has limited reporting utility.** If the distribution shape doesn't change week to week (and without trends, I can't tell), it's static decoration. The histogram becomes useful only when I can overlay this week's distribution against last week's and show the shift.

---

## Summary: Overall Dashboard Assessment

### Verdict: Strong Foundation, Clear Gaps

| Dimension | Rating | Notes |
|-----------|--------|-------|
| **Morning Triage** | 🟡 7/10 | KPIs and alert logic are excellent. No trends or time filtering is a critical gap. |
| **Coaching Prep** | 🟢 8.5/10 | Conversation detail view is outstanding. Best-in-class evidence linking. Missing agent-level aggregation. |
| **Weekly Reporting** | 🔴 5/10 | Good slice-by-call-reason analysis. Unusable for actual reporting without trends, deltas, or exports. |

### The #1 Product Insight

**The dashboard excels at depth but lacks breadth over time.** It's like having a microscope but no timeline. I can zoom into any single conversation beautifully, and I can see today's aggregate health clearly. But I cannot answer: "Are we getting better?" — which is the fundamental question my VP asks every Monday, and the fundamental question that justifies the QA function's existence.

### Top 5 Gaps, Prioritized

| Priority | Gap | Impact | Effort |
|----------|-----|--------|--------|
| **P0** | **Temporal trends** (week-over-week deltas, sparklines) | Blocks weekly reporting entirely | Medium |
| **P1** | **Date range filtering** (last 24h, last 7d, custom) | Blocks effective triage | Low |
| **P1** | **Agent-level aggregation** | Blocks coaching prioritization | Medium (needs data) |
| **P2** | **Export / report generation** | Manual workaround exists (screenshots) | Low |
| **P2** | **Cross-view navigation** (click call reason → filtered queue) | Minor friction, slows workflow | Low |

### Top 3 Things to Remove or Relocate

| Item | Current Location | Recommendation |
|------|-----------------|----------------|
| API Reference | Sidebar (always visible) | Move to separate "Developer" tab or documentation |
| Coaching Pattern Map | Quality Summary | Move to a separate "Coaching Analytics" tab |
| Score Distribution Histogram | Quality Summary | Move to "Analytics Deep Dive" tab or show only when comparing time periods |

### What I'd Tell the Product Team

> "This is the best conversation detail view I've seen in a QA tool — the evidence linking, the sentiment trajectory, the compliance checklist, the TL;DR insights. If you showed me one conversation in this tool, I'd be sold. But my job isn't reviewing one conversation — it's managing quality across 3,000 conversations a day, over weeks and months. Give me the time dimension and this goes from 'impressive prototype' to 'I'd actually use this every day.'"

---

*Review conducted September 2026*
*Dashboard version: Prototype v1 (batch scoring, pre-computed data)*
