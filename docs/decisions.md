# Decision Log — Conversation Quality Reviewer

Every meaningful design choice and its rationale, organized by category.
Living document — updated as we build.

---

## Dataset

### Why ABCD v1.1?
- **Decision**: Use ASAPP's own ABCD dataset (10,042 human-to-human customer service dialogues)
- **Alternatives considered**: MultiWOZ (too academic, restaurant/hotel domain), SGD (Google's, no brand alignment), synthetic data (no credibility)
- **Rationale**: Domain-relevant (contact center), shows research into ASAPP's work, rich annotations (kb.json, guidelines.json, scenario metadata) enable the hybrid compliance signal, and it's publicly available so demo is reproducible
- **Risk**: Panel may view it as "too easy" since it's their own data — mitigate by showing deep understanding of the annotations

### Why 200 LLM-scored conversations (not 100 or 500)?
- **Decision**: Pre-compute full 5-signal LLM scores on ~200 conversations, stratified ~20 per flow
- **Alternatives**:
  - 50-100: Too few to show meaningful distributions or filter by flow. Scatter plots and histograms look sparse.
  - 500+: ~$8-10 API cost, 90+ min compute time, diminishing returns for demo. No new insight at 500 that 200 doesn't show.
  - All 10K: ~$150+, 10+ hours, overkill for a prototype demo.
- **Rationale**: 200 is the sweet spot — enough for credible distributions per flow (10 flows × 20 each), fast enough to re-run if needed (~30 min, ~$3), and shows you thought about cost/scale tradeoff
- **What we'd say in production**: "This is a sampling strategy. In prod, you'd score 100% with async workers and cache aggressively."

### Why all 10K get heuristic scores?
- **Decision**: Run the efficiency signal (pure heuristic, no API calls) across all 10,042 conversations
- **Rationale**: It's instant (no API cost), gives the Overview dashboard real density, and demonstrates the tiered scoring philosophy — cheap signals run on everything, expensive signals run on a sample or on-demand

---

## Signals

### Why these 5 signals?
- **Decision**: Resolution Effectiveness, Conversation Efficiency, Policy Compliance, Customer Sentiment Trajectory, Agent Communication Quality
- **Rationale**: Maps to what contact center leaders actually care about:
  - Resolution → "Did we solve it?" (the bottom line)
  - Efficiency → "How much did it cost?" (handle time = #1 cost driver)
  - Compliance → "Did we follow the rules?" (legal/brand risk)
  - Sentiment → "Is the customer happy?" (CSAT predictor)
  - Communication → "Is the agent good?" (coaching & consistency)
- **Why not others considered**:
  - Transfer rate: Not in the ABCD data
  - First contact resolution: Can't determine from single conversations
  - Agent knowledge accuracy: Overlaps with compliance

### Why these weights? (Resolution 0.30, Compliance 0.25, Efficiency 0.15, Sentiment 0.15, Communication 0.15)
- **Decision**: Resolution and Compliance dominate; efficiency/sentiment/communication are supporting
- **Rationale**: In regulated industries (ASAPP's customers: airlines, insurance), resolution and compliance are non-negotiable. Efficiency/sentiment/communication are "how well" you did it. Weights are configurable per customer — an airline might weight compliance higher, a retail brand might weight sentiment higher.
- **What we'd say**: "These are defaults. In production, weights are customer-configurable."

### Where "good" is defined vs. left to calibration
- **The case study prompt asks**: "Someone has to decide what 'good' looks like before any of it can be automated or reported on." Our 5 signals answer this at two different levels of groundedness — and the gap is intentional.
- **Grounded signals (Efficiency, Compliance)**: These explicitly define "good" with concrete thresholds and formulas.
  - *Efficiency*: "Good" = turn count at or below subflow baseline (ratio ≤1.0), substantive turn ratio near 100%, agent:customer turn ratio between 0.8–1.3, action count within ±20% of baseline. A QA Manager can look at these numbers and say "I agree" or "I disagree" with specific values.
  - *Compliance*: "Good" = agent followed the expected action sequence from kb.json. Scored via completeness (50%), precision (30%), sequence order (10%), base (10%). Deviations are flagged; the LLM layer determines if deviations were justified. This is the most defensible signal because it's anchored to documented policy.
- **Uncalibrated signals (Resolution, Sentiment, Communication)**: These define scoring dimensions and evaluation criteria in their LLM prompts, but don't anchor what specific score levels (e.g., 0.3 vs. 0.7) look like with concrete examples.
  - *Resolution*: Prompt says "0=unresolved, 0.5=partial, 1.0=fully resolved" — but what counts as "partial"? If the agent processed a refund but didn't confirm the timeline, is that 0.5 or 0.7?
  - *Sentiment*: "1.0 = customer stayed happy, 0.0 = frustrated and never recovered" — but a customer who starts frustrated, gets resolved, and ends neutral could be 0.6 or 0.8 depending on the rubric.
  - *Communication*: Has 4 sub-dimensions with guiding questions (best of the three), but still no anchored examples per score level.
- **Why the gap is intentional**: Calibrating LLM-judged signals requires annotated examples from the customer's QA team — "this is what a 0.7 Resolution looks like at JetBlue." That's a customer onboarding activity, not a prototype feature. The prototype demonstrates the scoring mechanism; calibration is the business process that tunes it.
- **What production calibration looks like**:
  1. *Grounded rubrics*: Each score level gets 2–3 annotated example conversations, embedded as few-shot examples in the LLM prompt.
  2. *Weight configuration*: Signal weights become customer-configurable (JetBlue might weight Compliance at 40% for DOT regulations).
  3. *Calibration loop*: QA Managers review a sample, flag disagreements, and those become training data. Measure Cohen's kappa between LLM judge and human reviewer. Below 0.6 kappa = rubric needs revision.
  4. *Threshold-setting*: "Above Bar" at 0.80 is meaningless until a customer says "80% of our conversations should score above this line." That's a business SLA, not a default.
- **Why this matters for ASAPP**: The two grounded signals prove we *can* define "good" concretely. The three uncalibrated signals show we understand the mechanism but intentionally left calibration as a customer-facing process — because that's what CoachingAI does (moving QA managers from evaluating to defining standards).

### Why hybrid for compliance (but not others)?
- **Decision**: Compliance uses heuristic first (action sequence matching from kb.json), then LLM to adjust ±0.2
- **Alternatives**: Pure LLM (expensive, slow), pure heuristic (misses nuance like justified deviations)
- **Rationale**: Shows cost/speed awareness. The heuristic catches 80% of compliance issues (wrong action order, missing steps). The LLM handles the 20% that requires judgment (e.g., agent skipped a step but for a valid reason). This is the kind of tiered approach a production system would use.

### Why hard blocks only on Resolution and Compliance (not all 5 signals)?
- **Decision**: Only Resolution < 0.50 or Compliance < 0.50 triggers a hard block (mandatory review, sorted to top of queue). Low Sentiment, Communication, or Efficiency do not.
- **Rationale**: Hard blocks mean "drop everything and review this now." That's the right response for:
  - **Resolution failure** — the customer's problem wasn't solved. They'll call back, escalate, or churn. That's a fire.
  - **Compliance failure** — the agent skipped identity verification, gave wrong refund info, or violated policy. That's legal/regulatory risk, especially for ASAPP's customers (airlines, insurance, banks).
- **Why the other three don't qualify**:
  - *Sentiment < 0.50* — the customer was unhappy. Bad, but not an emergency. It's a coaching opportunity for the next 1:1, not something the QA Manager needs to triage at 7:30 AM.
  - *Communication < 0.50* — the agent was unclear or lacked empathy. Same — coaching, not triage.
  - *Efficiency < 0.50* — the call took too many turns. That's a process or training issue, not a specific conversation requiring immediate attention.
- **The design principle**: "Did something go wrong that needs to be fixed right now?" (hard block) vs. "Is there a pattern we should coach on over time?" (flag). If all 5 signals triggered hard blocks, the queue would be flooded and the concept would lose meaning. Hard blocks work because they're rare and urgent.

### Why single API call per signal (not per-turn)?
- **Decision**: Each LLM signal makes ONE Claude API call per conversation, not one per turn
- **Alternatives**: Per-turn calls (more granular), multi-call chains (agent-style reasoning)
- **Rationale**:
  - Cost: A 30-turn conversation scored across 3 LLM signals = 3 calls (ours) vs. 90 calls (per-turn)
  - Context: The LLM sees the full conversation, so it can reason about trajectory and context
  - Speed: 3 concurrent calls finish in ~2s vs. 90 sequential calls in ~60s
  - Tradeoff: We lose real-time per-turn streaming, but that's not the use case (batch review, not live monitoring)

---

## Architecture

### Why batch review, not streaming (and how it complements ASAPP's cascade)?
- **Decision**: Build a batch post-call quality reviewer, not a real-time streaming scorer
- **Alternatives**: Real-time scoring during the call, hybrid (real-time flags + batch deep analysis)
- **Rationale**: The use case is QA review — the QA Manager reviews conversations *after* they happen, identifies patterns, and makes coaching/process decisions. That's inherently batch. Real-time scoring serves a different user (the supervisor monitoring live calls) and a different decision ("intervene now" vs. "coach tomorrow").
- **ASAPP context**: ASAPP's streaming cascade already handles real-time — guardrails, compliance checks, escalation triggers, all running during the call. This quality reviewer is the complementary post-call layer. The same signals can serve both: compliance action-sequence matching can run in real-time as a guardrail *and* post-call for the quality score. The LLM judgment layer is batch-only because it needs full conversation context, which you only have after the call ends.
- **Integration pattern**: Conversations flow through the streaming cascade during the call. After the call ends, transcripts land in storage. The quality reviewer picks them up asynchronously — batch on a schedule, or event-driven for near-real-time scoring. Scores flow into the Supervisor Suite, customer analytics, or BI tools.
- **What to say**: "Batch and streaming aren't competing — they're complementary layers serving different decisions at different timescales. Real-time prevents harm in the moment. Batch finds patterns that drive systemic improvement. I built batch because the QA Manager's workflow is batch."

### Why FastAPI + Streamlit (not a single app)?
- **Decision**: Separate FastAPI backend (the API) + Streamlit frontend (the dashboard)
- **Alternatives**: Streamlit-only (simpler), Flask + React (over-engineered), Jupyter notebook (too casual)
- **Rationale**:
  - Shows production thinking — the API is the real product, the dashboard is one consumer
  - ASAPP sells to enterprises who integrate via API, not dashboards
  - Lets us demo API endpoints directly (curl) AND show a visual dashboard
  - Streamlit is fast to build, appropriate for a prototype

### Why Claude Sonnet (not Opus, GPT-4, or Haiku)?
- **Decision**: Use Claude Sonnet 4.6 for all LLM judge signals
- **Rationale**:
  - These are **structured scoring tasks** (read transcript → evaluate against criteria → return JSON), not open-ended creative reasoning. Sonnet handles this reliably.
  - **Cost**: 200 conversations × 4 LLM calls = ~800 calls. Sonnet ≈ $3, Opus ≈ $15. At production scale (10K+ conversations/day), this 5x difference compounds.
  - **Speed**: Sonnet responds in ~2s vs. Opus at ~8s. For the live demo, fast response = smooth demo.
  - **ASAPP alignment**: ASAPP builds cost-efficient AI for high-volume contact centers. Defaulting to the most expensive model signals misalignment with their product philosophy.
  - **Not GPT-4**: ASAPP uses Anthropic — would be tone-deaf to use a competitor's model.
  - **Not Haiku**: Might miss nuance in compliance edge cases and sentiment trajectory analysis.
- **Production tiering answer**: "I used Sonnet because these are structured evaluation tasks where Sonnet performs comparably to Opus. In production, I'd use a tiered approach — Haiku for initial screening, Sonnet for detailed scoring, Opus for calibration and edge cases where human-LLM agreement is low."

### Why pre-computed scores (not live scoring in demo)?
- **Decision**: Pre-score 200 conversations, save to `precomputed_scores.json`, load at demo time
- **Rationale**: Demo must be snappy — can't wait 2s per conversation in a 10-min window. Pre-computed data loads instantly. We still show the live scoring capability via the API endpoint (score 1-2 conversations live to prove it works).
- **Tradeoff acknowledged**: Pre-computed data could be stale if we change signal logic. Mitigate by re-running seed script after any signal changes.

### Why async with semaphore (not simple sequential)?
- **Decision**: Engine runs LLM signals concurrently via asyncio.gather with semaphore (max 5 concurrent)
- **Rationale**: 3 LLM signals per conversation can run in parallel (they're independent). Semaphore prevents rate-limiting. Sequential would 3x the latency for no benefit.

---

## Dashboard

### Why 3 views (Overview, Deep Dive, Comparison)?
- **Decision**: Three distinct dashboard views
- **Rationale**: Maps to three user personas/workflows:
  - **Overview**: QA manager reviewing shift performance ("how are we doing?")
  - **Deep Dive**: QA analyst investigating a specific conversation ("what happened here?")
  - **Comparison**: Coach preparing for agent feedback ("show me good vs. bad")
- **Why not more**: 10-min demo. Three views is the max you can walk through meaningfully.

### Why scatter plot of Resolution vs. Compliance?
- **Decision**: Feature a Resolution-vs-Compliance scatter in Overview
- **Rationale**: This reveals the most interesting agent archetypes:
  - High resolution + high compliance = ideal
  - High resolution + low compliance = "cowboy" (solves problems but breaks rules)
  - Low resolution + high compliance = "by-the-book" (follows rules but doesn't help)
  - This is the kind of insight that makes a QA manager say "I need this tool"

---

## Dashboard Design Rationale

### Why break down quality by call reason (not just aggregate)?
- **Decision**: The primary table in Quality Summary groups scores by call reason (flow), not just a single aggregate number.
- **Rationale**: Different call reasons have structurally different quality profiles, and the root cause — and the fix — is different for each.
  - If "Troubleshoot Site" has low resolution but "Account Access" is fine → the problem isn't "agents are bad." It's that the troubleshooting workflow is broken, or the knowledge base for that call type is incomplete.
  - If "Refund" calls have low compliance but "Shipping" calls don't → agents need retraining specifically on refund policy, not a general refresher.
  - Without the call reason breakdown, the reviewer just sees "78% average" and can't take targeted action.
- **What the reviewer does with it**: Identifies which call reason to escalate, and to whom:
  - Bad compliance in refunds → escalate to Training: "Retrain agents on refund return policy, especially membership-tier rules"
  - Bad resolution in troubleshooting → escalate to Product/Engineering: "The troubleshooting workflow or KB is incomplete — agents can't resolve because they don't have the right tools"
  - Bad sentiment across all call reasons → escalate to QA Lead: "Systemic empathy gap — consider communication coaching program"
- **JetBlue example**: If the QA Manager sees that "Flight Change" calls have 0.72 quality but "Baggage Claim" is at 0.91, she doesn't run a company-wide training. She digs into Flight Change, finds that agents are skipping the fare-difference disclosure step (compliance), and sends a targeted Slack to the team lead.

### Why show hard blocks alongside quality score?
- **Decision**: The table shows both the average quality score AND the hard block count per call reason.
- **Rationale**: A call reason can average 0.85 (Above Bar) while still having 12 individual conversations where resolution failed or compliance was violated. The average looks fine, but those 12 calls are fires that need individual review.
  - Average quality answers: "Is this call type generally healthy?"
  - Hard block count answers: "Are there specific calls I need to review RIGHT NOW?"
  - You need both. A flow with 0.85 average and 0 hard blocks = healthy, move on. A flow with 0.85 average and 12 hard blocks = the average is masking serious failures in specific conversations.
- **Example**: "Account Access" averages 0.88 with 3 hard blocks. The 3 hard blocks are conversations where the agent didn't verify identity (compliance violation). The average is fine because most agents do it right, but those 3 calls are potential security incidents that need immediate review regardless of the average.

### What does X% flagged mean for the reviewer?
- **Decision**: Show flagged count as "flagged/total (X%)" not just a raw number.
- **Rationale**: The percentage is both a workload signal and a severity signal:
  - **2% flagged (e.g., 16/800)**: Normal noise. The reviewer triages those 16 calls individually during their daily review. No systemic issue — just a few conversations that went sideways.
  - **5-10% flagged (e.g., 50/800)**: Elevated. The reviewer should look for patterns — is it the same subflow? Same time of day? Potentially a recent policy change that agents weren't trained on.
  - **15%+ flagged (e.g., 120/800)**: Systemic problem. The reviewer should NOT review 120 calls individually — that's not scalable. Instead, escalate to the operations manager: "Refund calls have a 15% failure rate. We need to look at the process, not individual agents." This is a workflow or training issue, not an agent issue.
- **Why percentage, not just count**: 12 flagged calls out of 100 (12%) is very different from 12 flagged out of 2,000 (0.6%). The raw number alone doesn't tell you whether this is a fire or normal variance.

### Why uniform 0.80 threshold for all signals (and why it's intentionally simplified)?
- **Decision**: All 5 signals use the same tier thresholds: 🟢 ≥0.80, 🟡 0.50–0.79, 🔴 <0.50.
- **Why this is a simplification**: In production, each signal should have its own threshold, and thresholds should differ by customer:
  - **Resolution** should have a higher bar (0.90+). An airline can't accept 20% unresolved calls.
  - **Communication** could have a lower bar (0.70). Not every agent needs to score high on empathy — sometimes efficiency matters more.
  - **Compliance** depends on the industry. Insurance = 0.95+ (regulatory risk). Retail = 0.75 might be fine.
- **Why we kept it uniform for the prototype**: Easy to explain, easy to read, and the real answer is that thresholds are customer-configurable. The prototype demonstrates the framework; the thresholds are a configuration decision, not an architecture decision.
- **What to say**: "In production, these thresholds are configurable per customer. An airline's compliance bar is different from a retailer's. The prototype uses a uniform 0.80 as a starting point, but the right thresholds come from calibration with each customer's QA team — you run a calibration sprint where the QA team reviews 200 calls, you measure where their pass/fail line falls, and you set the threshold there."

---

## Scope

### What we're explicitly NOT building
- Real-time/streaming scoring (this is batch review)
- User authentication or multi-tenancy
- Agent-level aggregation (would need agent IDs, ABCD doesn't have them)
- Audio/voice features (text-only, but tradeoffs.md discusses what changes for voice)
- Custom signal configuration UI
- Persistent database (JSON file storage is fine for prototype)

---

## Talk It Out — Don't Build It

Features that are MORE impressive to talk about than to demo, because building them
would cost hours for 30 seconds of demo time, while talking about them shows product
maturity and production thinking.

### Human Feedback / Coach's Notes
- **What it would be**: Text input on the Conversation Detail view where the QA manager writes coaching feedback per conversation. Feedback is saved, linked to the agent, and feeds into performance reviews.
- **Why talk, don't build**: Building a feedback UI (text input, save, retrieve, display) is 2+ hours for a feature you'd demo for 30 seconds. The prototype has no persistence layer or user auth — feedback would disappear on restart.
- **What to say**: "In production, this screen would have a 'Coach's Notes' field where the QA manager writes feedback, which feeds into agent performance reviews. The feedback loop also becomes a calibration data point — if a human disagrees with a score, that signal tunes the LLM judge."
- **What we DO build**: A disabled "Add Feedback" button in the UI as a visual hook so the panel can see you thought about it.

### Calibration Loop (LLM Judge vs. Human Agreement)
- **What it would be**: A calibration pipeline where 3 QA analysts independently score 200 conversations on the same 5 signals, we measure inter-annotator agreement (Cohen's kappa), then measure LLM-vs-human agreement per signal. Signals where the LLM disagrees with human consensus get rubric tuning.
- **Why talk, don't build**: Calibration requires human-labeled data we don't have. The pipeline itself (from voice-agent-ops: `calibration.py`) is straightforward — the hard part is getting the human labels. Building a mock would be dishonest; talking about it shows you've done it before.
- **What to say**: "The scores you see are directional, not ground truth. In production, I'd run a calibration loop: have 3 QA analysts independently score 200 conversations on the same 5 signals, measure inter-annotator agreement with Cohen's kappa, then measure LLM-vs-human agreement. Where the LLM disagrees with consensus, we tune the rubric. Where humans disagree with each other, we tighten the signal definition. This is ongoing, not one-time — I built exactly this at Mudflap for our voice agent evals."
- **What we DO build**: A "Judge Info" sidebar panel showing which signals are LLM-judged vs. heuristic, and "Calibration status: Not yet calibrated — scores are directional." Honest, shows maturity.

### Grounded Rubrics / Eval Criteria Documentation
- **What it would be**: A shared rubric document that both LLM judges and human reviewers score against — specific enough that two humans would give the same score to the same conversation. Versioned, with examples of "this is a 0.3" vs. "this is a 0.8" for each signal.
- **Why talk, don't build**: The rubric is embedded in our LLM prompts already (the scoring criteria in each signal's prompt). The problem isn't writing a rubric — it's validating that the rubric matches what humans actually think "good" means. That requires iteration with real QA teams, not a prototype.
- **What to say**: "The hardest part of quality scoring isn't the model — it's aligning on what 'good' means. Even human reviewers disagree. In production, I'd start with a draft rubric, have the QA team score 50 conversations against it, measure disagreement, refine the rubric, and repeat until kappa exceeds 0.7. Only then do you train the LLM judge against it. The rubric is a living document, not a spec."
- **Connects to**: ASAPP's CoachingAI product, which scores compliance, topic mastery, and tool mastery — they've clearly built this calibration loop internally.

### Regression Detection
- **What it would be**: Compare current scoring run against a baseline. If any signal drops more than 5 percentage points from the last passing run, flag as regression even if absolute score is still above threshold.
- **Why talk, don't build**: We only have one scoring run (no historical baseline to compare against). The concept is powerful but needs time-series data.
- **What to say**: "Absolute thresholds catch failures; regression detection catches degradation. If compliance was 0.85 last week and 0.78 this week, that's a 7-point drop — still above bar, but a trend you want to catch before it hits 0.50. I built this into a previous voice agent deployment pipeline."

### Agent-Level Aggregation
- **What it would be**: Aggregate scores by individual agent to identify coaching targets. "Agent Smith resolves 90% of cases but has low empathy scores — specific coaching opportunity."
- **Why talk, don't build**: ABCD dataset doesn't have agent IDs. Can't demo it without the data.
- **What to say**: "In production with real data, you'd aggregate by agent to identify coaching targets. 'Agent Smith resolves 90% of cases but empathy is at 0.35 — here's a specific coaching opportunity with three example conversations.' That's the workflow that makes CoachingAI valuable."

---

## Dashboard UX Decisions (Polish Pass)

### Why "Failure Pattern Map" instead of "Resolution vs. Compliance"?
- **Decision**: Renamed the Resolution-vs-Compliance scatter plot to "Failure Pattern Map" with quadrant shading, actionable labels, and per-quadrant counts.
- **Rationale**: The original title described the axes, not the insight. The value of this chart is that it reveals **failure patterns by call reason** (since the ABCD dataset lacks agent IDs, dots are conversations, not agents):
  - **Top-right** (high resolution + high compliance) = No action needed.
  - **Bottom-right** (high compliance + low resolution) = Resolution gap → improve tools / knowledge base.
  - **Top-left** (high resolution + low compliance) = Policy gap → update process / retrain on policy. **Most dangerous quadrant** in regulated industries — the customer is happy but the company is exposed.
  - **Bottom-left** = Both failing → escalate / investigate root cause.
- Each quadrant label includes the **action** ("→ improve tools / knowledge base"), not just the diagnosis. Quadrant counts and auto-generated insight ("Top pattern: 28 flagged conversations in Manage Account") give the QA Manager a clear next step.
- **Why not "Coaching Pattern Map"**: Without agent IDs, this can't show coaching targets per agent. Reframing as "Failure Pattern Map" is honest about what the data supports. In production with agent IDs, this becomes the coaching prioritization view — a great "talk about" point.

### Why Quality Trend line chart (replaced Score Distribution histogram)?
- **Decision**: Replaced the Score Distribution histogram with a Quality Trend line chart showing daily average quality score over time, with threshold lines and an auto-generated trend insight.
- **Rationale**: The histogram was descriptive but not actionable — it duplicated the KPI cards (tier counts) without telling the QA Manager what to *do*. The histogram answered "what's the shape of our distribution?" which is a data science question, not a QA Manager question. The Quality Trend chart answers "are we getting better or worse?" — one of the QA Manager's core daily questions:
  - Sustained dip → investigate what changed (new policy? new agents? broken workflow?)
  - Improving trend → training or process changes are working
  - Stable → no action needed
- Auto-generated insight below the chart compares last 3 days vs. prior period and states the verdict, so the QA Manager doesn't have to interpret the chart visually.

### Why emoji + text instead of progress bars for Quality Score?
- **Decision**: Replaced `st.column_config.ProgressColumn` with a formatted text column showing `🟢 0.85` / `🟡 0.72` / `🔴 0.45`.
- **Rationale**: Streamlit's `ProgressColumn` doesn't support conditional colors — all bars render in the same default color (pink/red). This made "Above Bar" conversations look identical to "Below Bar" ones, defeating the purpose. The emoji + number format is actually more scannable for triage — QA Managers scan for red/yellow first, then look at the number. This matches the tier system used everywhere else in the dashboard.

### Why ±0.02 trend stability band (not ±0.05)?
- **Decision**: Trend arrows show when quality shifts more than ±0.02 between periods. Anything within that band shows "— stable."
- **Why 0.02, not 0.05**: Demo-driven. With ~20 conversations per flow and simulated prior-period data, a 0.05 band suppresses nearly every trend — the column would read "— stable" for every row and the feature would look dead during the demo. 0.02 keeps the trend column visually active so the panel can see how it works.
- **Why this is wrong for production**: At scale (thousands of conversations per flow), a 0.02 shift is normal variance, not a signal worth acting on. The right approach isn't a hardcoded band at all — it's a statistical significance test based on sample size and confidence intervals. A flow with 20 conversations needs a much wider band than a flow with 2,000.
- **What to say**: "The stability band is intentionally tight for the demo so you can see the feature in action. In production, I'd replace the fixed band with a significance test — the threshold adapts to sample size so you only see trends that are statistically meaningful, not noise."

### Why sortable flow table?
- **Decision**: Added a sort toggle above the Quality by Flow table with three options: Quality (low→high), Flagged % (high→low), Hard Blocks (high→low).
- **Rationale**: Different triage workflows need different sort orders:
  - **Quality low→high** (default): "Which call types are worst?" — identify systemic issues
  - **Flagged % high→low**: "Where is my review workload?" — the QA Manager has 2 hours for review, start where the most conversations need attention
  - **Hard Blocks high→low**: "What needs attention RIGHT NOW?" — compliance violations and resolution failures can't wait
- The previous table was string-sorted, so "3/10 (30%)" sorted alphabetically before "16/800 (2%)" — misleading.

### Why 2 views instead of 3?
- **Decision**: Removed the standalone "Conversation Detail" tab. The dashboard now has 2 views: Quality Summary and Review Queue.
- **Rationale**: The Conversation Detail tab duplicated the Review Queue's inline detail view. Having both created a confusing question: "Where do I look at a conversation?" Two views = simpler mental model and a cleaner demo narrative:
  1. **Quality Summary** answers: "How are we doing?"
  2. **Review Queue** answers: "Which calls need attention?" → click → "What happened in this call?"
- The direct-lookup use case (type a conversation ID) is now handled by a search box at the top of the Review Queue.

### Why master-detail navigation in Review Queue?
- **Decision**: Clicking "Review →" replaces the list with the conversation detail view. A "← Back to Queue" button returns to the list.
- **Rationale**: This is the standard pattern from email clients and ticketing tools (Zendesk, Jira, Gmail). The previous design rendered the detail *below* all rows, which meant the QA Manager had to scroll past 20 rows of queue items to reach the detail. Master-detail navigation:
  - Eliminates scrolling — the detail fills the screen
  - Preserves context — "← Back" returns to the same filtered/sorted queue
  - Matches the QA Manager's existing mental model from tools they already use

### Key Insights TL;DR and Review-to-Detail click-through
- **Decision**: The conversation detail view leads with a "Key Insights" section — plain-language findings sorted by severity — before showing the score card, radar chart, and transcript.
- **Rationale**: The QA Manager's first question is "What went wrong?" not "What's the radar chart?" The TL;DR answers that in 2 seconds. If they need the detail (for coaching prep or compliance audit), they scroll down. This mirrors how a medical chart works: chief complaint first, then vitals, then full history.

### Why subflow breakdown replaces flow table when filtered
- **Decision**: When a specific call reason is selected, the Quality by Call Reason table switches to a Quality by Subflow table instead of showing a redundant 1-row flow table.
- **Rationale**: A 1-row table adds no information — the QA Manager already knows the call reason because they just filtered to it. The subflow breakdown answers the next question: "Within Manage Account, which subflows are driving the quality issues?" For example, if "Manage Account" has 42% flagged, is that evenly distributed across subflows, or is "change_password" driving it? The answer determines the coaching action: retrain on one specific workflow vs. systemic process change.

### Why Top Issues clustering
- **Decision**: When filtered to a specific call reason, show a "Top Issues" section with signal failure counts (sorted by severity) and top missing compliance actions (aggregated across all conversations).
- **Rationale**: "Compliance is bad" is not actionable. "Agents skip `validate-purchase` in 28 conversations" is. The signal failure ranking tells the QA Manager which dimension to focus on. The missing compliance actions turn an abstract score into a specific training action — this is what gets copied into the coaching Slack message or training deck. Without this, the QA Manager has to click into 28 individual conversations to discover the same pattern.

### Why API reference in dashboard sidebar
- **Decision**: Added an expandable API reference in the sidebar showing all endpoints, methods, and an example curl command.
- **Rationale**: The case study prompt requires a "clear contract." The dashboard is one consumer of the API — the sidebar reference shows the panel that we designed the API first and the dashboard second. It also makes the demo smoother: instead of switching to Swagger UI or a terminal, the interviewer can see the contract in context. The API is the real product; the dashboard is the demo vehicle.
