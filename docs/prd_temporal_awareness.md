# Product Lead Response: Prioritization & P0 PRD

**Author**: Product Lead, Voice — ASAPP
**Input**: QA Manager Dashboard Review (`docs/qa_manager_review.md`)
**Date**: September 2026

---

## Part 1: Prioritization Rationale

The QA Manager's review is sharp. She correctly identified the core problem: **the dashboard is a microscope without a timeline.** But I'd re-prioritize some items based on what drives customer adoption, ASAPP's competitive positioning, and effort/impact tradeoffs.

### P0 — Must ship before next customer demo

| # | Feature | QA Manager Priority | Why I'm making it P0 |
|---|---------|-------------------|---------------------|
| 1 | **Temporal trends** (deltas + sparklines on KPIs and call reason table) | P0 | Agree. Without this, the dashboard is a one-time tool, not a daily habit. Daily habit = retention = contract renewal. Also directly supports CoachingAI's core narrative: "Are coaching interventions working?" |
| 2 | **Date range filtering** (Last 24h / 7d / 30d / custom) | P1 | **Promoting to P0.** The QA Manager listed this as P1 but it's inseparable from temporal trends — you can't show a delta without defining "compared to what?" These are the same feature. Morning triage needs "last 24h." Weekly reporting needs "last 7d." They're different time windows into the same data. |
| 3 | **Cross-view navigation** (click call reason row → filtered Review Queue) | P2 | **Promoting to P0.** The QA Manager called this "minor friction." I disagree. This is a broken workflow loop. She sees "Refund calls have low compliance" in Summary, then has to mentally carry that context, switch views, and manually set filters. Every manual step is a place where the user drops off or loses context. More importantly: this is ~2 hours of engineering work for a massive usability gain. Low effort, high signal that we built this for the QA Manager, not for ourselves. |

### P1 — Next sprint after P0

| # | Feature | QA Manager Priority | Rationale |
|---|---------|-------------------|-----------|
| 4 | **Volume context** (conversation count as prominent column in call reason table) | Not explicitly prioritized | Low effort, high value. Quality scores without N are misleading. "0.92 quality on 3 calls" vs "0.68 quality on 500 calls" — the latter is actually more important. The QA Manager mentioned this under weekly reporting but it matters everywhere. 30 minutes of work. |
| 5 | **Export / report generation** (PDF summary or clipboard copy) | P2 | The QA Manager's workaround (screenshots) works but is embarrassing for a product we're selling to Fortune 500 companies. A basic "Copy Summary" or "Download PDF" removes a real pain point from the weekly reporting workflow. |
| 6 | **Sidebar cleanup** (remove API Reference, relocate scatter plot and histogram) | Not prioritized | The QA Manager is right: API Reference is developer-facing noise in a QA tool. Coaching Pattern Map and Score Distribution histogram belong in a separate analytics tab, not the daily triage view. This is information architecture, not feature work — but it signals product maturity. |

### P1 (Design Only) — Design now, build when data allows

| # | Feature | QA Manager Priority | Rationale |
|---|---------|-------------------|-----------|
| 7 | **Agent-level aggregation** | P1 | The QA Manager is right that this blocks coaching prioritization. But I'm deliberately scoping this as "design only" for the prototype because: (a) ABCD dataset lacks agent IDs — we can't demo it with real data, (b) this is the core value prop of CoachingAI — we should design it carefully with the CoachingAI team, not bolt it on, (c) a half-built agent view is worse than talking about a well-designed one. **For the presentation**: show wireframes and data model, explain the coaching workflow it enables, reference CoachingAI alignment. |

### Deferred — Important but not blocking adoption

| # | Feature | Rationale |
|---|---------|-----------|
| 8 | Coaching session builder (bookmark/tag conversations) | Valuable but requires persistence layer we don't have. Talk about it. |
| 9 | Comparative conversation view (side-by-side) | High-effort UX work. Coaching prep already scores 8.5/10 — diminishing returns. |
| 10 | Alert/notification configuration | Requires infrastructure (webhook/Slack integration). Production feature, not prototype. |
| 11 | Suggested coaching talking points (LLM-generated) | Interesting but scope-creepy. The Key Insights TL;DR already covers 80% of this. Revisit after calibration is in place. |
| 12 | Custom quality targets per signal/call reason | Configuration complexity. Talk about it in the presentation; the threshold framework already supports it architecturally. |

### Why this ordering?

**ASAPP's competitive moat is not "we score conversations."** Observe.AI, NICE CXone, Verint — they all do that. ASAPP's moat is **cost-efficient AI at scale that changes QA manager behavior from evaluating to coaching.** The P0 features directly serve this:

- **Temporal trends** prove coaching works → QA manager becomes an advocate → contract renewal
- **Date filtering** makes the dashboard a daily operating tool → habit formation → stickiness
- **Cross-view navigation** completes the triage-to-action loop → time saved → ROI story for procurement

The P1 items (volume context, export, sidebar cleanup) are polish that compounds trust. The design-only agent aggregation investment ensures we don't paint ourselves into a corner when CoachingAI integration happens.

---

## Part 2: P0 PRD — Temporal Awareness & Workflow Navigation

### Overview

**Problem**: The dashboard provides a point-in-time snapshot with no temporal context. The QA Manager cannot answer "Are we getting better?", cannot compare today to yesterday, and cannot navigate from an aggregate insight to the specific conversations driving it.

**Solution**: Add time-windowed data views with delta indicators, date range filtering, and clickable navigation from Quality Summary rows to filtered Review Queue.

**Success Criteria**:
- QA Manager can complete morning triage (identify regressions, decide escalation) in under 60 seconds
- QA Manager can answer "Is quality improving?" with data in under 10 seconds
- QA Manager can go from "Refund compliance is low" to reviewing the specific conversations in 2 clicks

**Dependencies**:
- Timestamped scoring data (currently precomputed_scores.json has no timestamps — needs migration)
- Sufficient historical data to compute deltas (minimum: 2 scoring runs across different time windows)

---

### Feature 1: Date Range Selector

#### What

A time window selector in the sidebar (above the existing Call Reason filter) that controls all dashboard views.

#### Behavior

**Preset Options** (radio buttons):
- Last 24 hours
- Last 7 days (default)
- Last 30 days
- All time

**How it works**:
- All KPI cards, tables, charts, and Review Queue filter to conversations scored within the selected window
- The comparison period is automatically the equivalent preceding window (e.g., "Last 7 days" compares to the 7 days before that)
- If insufficient data exists for comparison, show the current value without a delta and display a subtle note: "Not enough history for comparison"

#### Data Model Change

Add `scored_at` timestamp to `ConversationResult`:

```python
class ConversationResult(BaseModel):
    convo_id: int
    flow: str
    subflow: str
    scores: dict[str, SignalScore]
    overall_score: float
    flags: list[str]
    scored_at: datetime  # NEW — when this conversation was scored
```

Update `precomputed_scores.json` schema to include `scored_at` per result. For the prototype, backfill with synthetic timestamps distributed across the past 30 days to simulate realistic data.

#### Why this design

- **Presets over custom date picker**: Custom date pickers are slow to use and overkill for the two workflows that matter (morning triage = 24h, weekly reporting = 7d). Presets match how the QA Manager actually thinks about time.
- **Auto-comparison window**: Eliminates a second date picker. The QA Manager doesn't want to configure "compare period" — she wants to see the delta. The system should figure out the comparison window.
- **All time as an option**: Supports one-off deep dives and the demo use case (show all pre-computed data).

---

### Feature 2: Delta Indicators on KPI Cards

#### What

Each of the 4 top-line KPI cards shows the current value plus a delta compared to the previous equivalent period.

#### Behavior

**Current cards** (unchanged values, new delta row):

```
┌─────────────────────┐  ┌─────────────────────┐
│ Overall Quality      │  │ Pass Rate            │
│ 81.2%               │  │ 87%                  │
│ ▲ 3.1% vs last 7d   │  │ ▲ 2% vs last 7d     │
└─────────────────────┘  └─────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐
│ Hard Blocks          │  │ Needs Review         │
│ 8                    │  │ 34                   │
│ ▼ 4 vs last 7d      │  │ ▼ 12 vs last 7d     │
└─────────────────────┘  └─────────────────────┘
```

**Delta formatting rules**:
- **Positive direction** (quality up, hard blocks down): green text, ▲/▼ arrow
- **Negative direction** (quality down, hard blocks up): red text, ▲/▼ arrow
- **No change or insufficient data**: gray text, "—" or "No prior data"
- Note: For Hard Blocks and Needs Review, *down* is good (green) and *up* is bad (red). The color reflects business meaning, not mathematical direction.

#### Why this design

- **Deltas are the single most requested feature** across all three workflows. The QA Manager explicitly said: "Without the delta, I can't prioritize."
- **"vs last 7d" label**: Makes the comparison explicit. No ambiguity about what the number is compared to.
- **Color encoding on direction**: At 7:30 AM, the QA Manager needs to see green/red before she reads the number. Color → gut reaction → read number → decide.

---

### Feature 3: Call Reason Table with Trend Indicators

#### What

The Quality by Call Reason table gains a new "Trend" column showing the directional change in quality score for each call reason.

#### Behavior

**New column: Trend**

| Status | Call Reason | Quality Score | Trend | Biggest Gap | Hard Blocks | Flagged |
|--------|------------|--------------|-------|-------------|-------------|---------|
| 🔴 | Refund | 🔴 0.62 | ▼ 0.08 | Compliance (0.45) | 🔴 5 | 12/40 (30%) |
| 🟡 | Troubleshoot | 🟡 0.71 | ▲ 0.05 | Resolution (0.58) | — | 8/35 (23%) |
| 🟢 | Account Access | 🟢 0.88 | — | Sentiment (0.76) | — | 2/30 (7%) |

**Trend column rules**:
- Shows absolute score change vs. prior period
- Red ▼ for decline > 0.02, green ▲ for improvement > 0.02, gray — for stable (±0.02)
- Sortable: Add "Biggest Decline" as a 4th sort option (joins existing Quality, Flagged %, Hard Blocks)

**New sort option: "Biggest Decline"**
- Sorts by negative trend delta (largest decline first)
- This is the morning triage sort: "What got worse overnight?"

#### Why this design

- **Absolute delta, not percentage**: "Down 0.08 points" is more interpretable than "down 11.4%" when the base is 0.70. Contact center QA teams think in score points.
- **±0.02 stability band**: Prevents noise from triggering false alarms. Small fluctuations in a few conversations shouldn't show as a trend.
- **"Biggest Decline" sort**: Directly serves the triage workflow. The QA Manager's first question is "What got worse?" — this sort answers it instantly.

---

### Feature 4: Cross-View Navigation (Summary → Queue)

#### What

Call reason rows in the Quality Summary table become clickable. Clicking a row navigates to the Review Queue pre-filtered to that call reason, with the relevant signal failure highlighted.

#### Behavior

**Click interaction**:
1. QA Manager sees "Refund → Compliance (0.45)" in the Biggest Gap column
2. She clicks the "Refund" row
3. Dashboard switches to Review Queue view
4. Call Reason filter auto-set to "Refund"
5. A new signal filter appears, pre-set to "Compliance flags" (derived from Biggest Gap)
6. Review Queue shows only refund conversations with compliance issues, sorted by severity

**Signal filter** (new control in Review Queue):
- Dropdown: "All signals" (default), "Resolution flags", "Compliance flags", "Sentiment flags", "Communication flags"
- Filters to conversations where that specific signal triggered a flag
- This control is useful independently of the cross-view navigation — a QA Manager might want to review all compliance-flagged conversations regardless of call reason

**Back navigation**:
- "← Back to Summary" link at top of Review Queue when arriving via cross-view click
- Preserves the QA Manager's mental context: "I was looking at the summary, drilled into refunds, now I'm going back"

#### Why this design

- **Click the row, not a button**: Reduces visual clutter. The entire row is the affordance. Cursor changes to pointer on hover.
- **Auto-set both filters (call reason + signal)**: The QA Manager clicked because of a specific insight ("Refund compliance is bad"). Setting both filters preserves that context. If she only wanted all refund conversations, she'd use the sidebar filter.
- **Signal filter as independent control**: Even without cross-view navigation, filtering the queue by signal type is useful. "Show me all conversations with sentiment deterioration" is a valid workflow (coaching prep for empathy training). The cross-view click just pre-sets it.
- **"← Back to Summary" link**: Prevents disorientation. Without it, the QA Manager might not remember how she got to this filtered view. The back link closes the loop.

---

### Implementation Notes

#### Data Generation for Demo

The prototype uses pre-computed scores without timestamps. To demo temporal features:

1. **Backfill timestamps**: Distribute the existing ~200 scored conversations across the past 30 days with realistic patterns (more on weekdays, fewer on weekends, slight clustering during business hours).

2. **Simulate trend data**: Score an additional ~100 conversations and assign them to the "prior period" with slightly different score distributions. This creates believable deltas without requiring a real production pipeline.

3. **Seed script update**: Modify `scripts/seed_data.py` to:
   - Add `scored_at` to each `ConversationResult`
   - Assign synthetic timestamps
   - Optionally generate a "baseline" period for comparison

#### Architecture Impact

- **No new API endpoints needed**: The existing `/conversations` and `/summary` endpoints add an optional `?from=&to=` query parameter. Filtering happens server-side.
- **Dashboard state**: Date range and signal filter stored in `st.session_state` alongside existing view and call reason filter.
- **Cross-view navigation**: Uses `st.session_state` to pass filter context between views. No URL routing needed (Streamlit limitation).
- **Performance**: Filtering ~200-300 pre-computed results by timestamp is instant. No caching changes needed at prototype scale.

#### Effort Estimate

| Feature | Effort | Notes |
|---------|--------|-------|
| Data model + timestamp backfill | 2-3 hrs | Modify models, update seed script, regenerate data |
| Date range selector (sidebar) | 1-2 hrs | Sidebar widget + filtering logic |
| KPI delta indicators | 2-3 hrs | Comparison period calculation + delta formatting |
| Call reason table trend column | 2-3 hrs | Delta computation per call reason + new sort option |
| Cross-view navigation | 2-3 hrs | Click handler + session state + signal filter |
| Testing + polish | 2-3 hrs | Edge cases (no prior data, single conversation in period, etc.) |
| **Total** | **~12-16 hrs** | |

---

### What This Unlocks

After P0 ships, the dashboard transforms from a **reporting artifact** into a **daily operating system**:

| Workflow | Before P0 | After P0 |
|----------|-----------|----------|
| **Morning Triage** | "Here are today's numbers" (no context) | "Quality dropped 5pts overnight, driven by refund compliance — click to see the 8 conversations" |
| **Coaching Prep** | Filter by call reason, scroll through queue | Click the problem row in Summary → land on exactly the conversations that need coaching |
| **Weekly Reporting** | Screenshot static numbers | "Quality improved from 0.76 to 0.81 over the past 7 days. Hard blocks decreased from 12 to 8. Refund compliance improved 0.08 pts after Tuesday's retraining." |

The QA Manager's own words: *"Give me the time dimension and this goes from 'impressive prototype' to 'I'd actually use this every day.'"*

That's what P0 delivers.

---

*PRD authored September 2026*
*Informed by QA Manager persona review and ASAPP CoachingAI product alignment*
