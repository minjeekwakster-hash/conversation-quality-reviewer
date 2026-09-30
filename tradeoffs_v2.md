# Tradeoffs Note — Conversation Quality Reviewer

## 1. Why These Metrics

Five signals, each mapped to a question contact center leaders actually ask:

| Signal | The Question It Answers | Why It Matters |
|---|---|---|
| Resolution Effectiveness | "Did we solve it?" | The bottom line — an unresolved call is a repeat call |
| Conversation Efficiency | "How much did it cost?" | Handle time is the #1 cost driver in contact centers |
| Policy Compliance | "Did we follow the rules?" | Legal and brand risk, especially in regulated industries (airlines, insurance) |
| Customer Sentiment | "Is the customer happy?" | Leading indicator of CSAT and churn |
| Agent Communication | "Is the agent coachable?" | Identifies specific skill gaps for targeted coaching |

**What I considered and rejected:**
- *Transfer rate* — not in the ABCD dataset
- *First contact resolution* — can't determine from single conversations without session linking
- *Agent knowledge accuracy* — overlaps too heavily with compliance; not a distinct coaching lever

**Why these weights** (Resolution 0.30, Compliance 0.25, others 0.15 each): In regulated industries — ASAPP's customers — resolution and compliance are non-negotiable. The other three signals tell you *how well* the agent did it. In production, weights are customer-configurable: an airline weights compliance higher, a retail brand weights sentiment higher.

**Why the heuristic/LLM split:**
- **Efficiency** is pure heuristic — turn count and action sequences are structural. A language model adds no value over counting.
- **Compliance** is hybrid — action sequence matching catches 80% of violations; the LLM handles justified deviations that require judgment.
- **Resolution, Sentiment, Communication** are LLM-based — whether an agent actually resolved an issue requires semantic understanding that heuristics can't capture.

The split matters for explainability. In regulated industries, "the rule caught the deviation, and the model confirmed it was justified" is a stronger answer than "the model said so."

## 2. What I'd Harden for Production

**Tiered scoring pipeline.** The prototype scores every conversation with 4 LLM calls (Resolution, Sentiment, Communication, Compliance adjustment) plus 1 heuristic signal (Efficiency) — **~$0.028 per conversation** on Claude Sonnet. At scale, that compounds:

**Cost per conversation by model:**

| Model | Input $/1M | Output $/1M | Cost/Convo | Why Use It |
|---|---|---|---|---|
| Haiku | $1 | $5 | ~$0.009 | Screening & simple classifications |
| **Sonnet** | **$3** | **$15** | **~$0.028** | **Production scoring (current)** |
| Opus | $15 | $75 | ~$0.14 | Calibration tiebreakers & edge cases |

**Cost at scale — full LLM vs. tiered:**

| Daily Volume | Full LLM (Sonnet) | Tiered (15% LLM) | Heuristic Only |
|---|---|---|---|
| 1K convos | $28/day | ~$4/day | $0 |
| 10K convos | $275/day | ~$41/day | $0 |
| 50K convos | $1,375/day | ~$206/day | $0 |
| 100K convos | $2,750/day | ~$413/day | $0 |

*Basis: 4 LLM calls/convo × ~1,050 input tokens + ~250 output tokens per call. ABCD conversations average 24 turns / ~266 transcript tokens. Tiered assumes heuristic on 100%, LLM on flagged (~5%) + 10% random sample.*

Production needs tiers:
- **Tier 1 (100% of conversations):** Heuristic signals only — instant, no API cost, flags outliers.
- **Tier 2 (flagged + 10% sample):** Full LLM scoring. At 100K conversations/day, ~15K get LLM scoring → **~$413/day** with Sonnet.
- **Tier 3 (on-demand):** Deep analysis triggered by QA analysts. Negligible volume.

**Compare to manual QA:** A full-time QA analyst costs ~$60-80K/year and reviews ~20-30 conversations/day. The tiered automated system covers 100K conversations for ~$12K/month — less than one analyst's salary while covering 3,000x more conversations.

This mirrors how ASAPP's cascade architecture already works — cheap models filter, expensive models refine.

**Customer-configurable thresholds.** The prototype uses a uniform 0.80 for all signals. In production, each signal needs its own threshold, and thresholds differ by customer:
- Resolution should have a higher bar (0.90+) — an airline can't accept 20% unresolved calls.
- Communication could have a lower bar (0.70) — not every agent needs high empathy scores.
- Compliance depends on the industry — insurance = 0.95+ (regulatory risk), retail = 0.75 might be fine.

The right thresholds come from calibration with each customer's QA team, not from defaults.

**Agent-level aggregation.** The prototype can't do this (ABCD lacks agent IDs), but in production, aggregating by agent is what makes the tool a coaching product: "Agent Smith resolves 90% of cases but empathy is at 0.35 — here are three example conversations for your next 1:1."

**Persistent storage and async processing.** Replace JSON file storage with a real database. Score conversations asynchronously via a job queue, not synchronously per request.

**Voice/audio signals.** This prototype is text-only. For ASAPP's voice product, additional signals become available — prosody for sentiment (tone detects frustration before words do), dead air and hold time for efficiency (the real cost drivers), speech rate and filler words for communication quality. ASAPP's speech-to-speech models could score audio directly without transcription, eliminating ASR errors. The signal framework stays the same — swap text-based signal computers for audio-based ones.

## 3. What Changes for Voice/Audio

This prototype is text-only. For ASAPP's voice product, the signal framework stays the same — what changes is the inputs and what you can detect:

| Text Signal | Voice Equivalent | What It Adds |
|---|---|---|
| Sentiment (text) | Sentiment (text + prosody) | Tone of voice detects frustration before words do — "that's fine" said sarcastically reads neutral in text but negative in audio |
| Efficiency (turn count) | Efficiency (handle time + dead air + hold time) | Dead air and hold time are the real cost drivers — an extra turn in text is milliseconds, but 30 seconds of silence in a phone call is 30 seconds of customer frustration |
| Communication (clarity) | Communication (speech rate, filler words, interruptions) | Excessive "ums," rapid speech when uncertain, talk-over ratio — these are coachable agent behaviors invisible in text |
| — (not available) | Interaction Dynamics (new signal) | Who's talking over whom, response latency, silence gaps. Inherently audio-based, no text equivalent |

**S2S model opportunity**: ASAPP's speech-to-speech models could score audio directly without transcription, eliminating ASR errors and capturing paralinguistic features. The quality reviewer's signal framework stays the same — swap text-based signal computers for audio-based ones. This is one of the most compelling production extensions and it's unique to ASAPP because you have the in-house models to do it.

**Why I didn't build this**: The ABCD dataset is text. Building voice features on text data would be dishonest. The signal framework is modular by design — each signal is a separate computer with a defined interface — specifically so that text-to-voice migration is a signal swap, not a rewrite.

## 4. What I'd Measure to Know It's Working

**LLM-vs-human agreement.** Have 3 QA analysts independently score 200 conversations on the same 5 signals. Measure inter-annotator agreement (Cohen's kappa). Then measure LLM-vs-human agreement per signal. Where the LLM disagrees with human consensus, tune the rubric. Where humans disagree with each other, tighten the signal definition. Target: kappa > 0.7 per signal.

**Score-CSAT correlation.** If the reviewer scores a conversation highly but the customer gives a low CSAT, something is wrong. Track this correlation over time — it's the external validation that scores are meaningful.

**Drift monitoring.** LLM scoring can drift as models are updated. Run the ground truth set through the pipeline monthly and alert on score distribution shifts. Regression detection: if any signal drops more than 5 percentage points from the last passing run, flag it — even if the absolute score is still above threshold.

**Calibration by customer.** Different customers have different standards. Measure agreement separately per customer and recalibrate when it drops below threshold.

**Operational metrics.** Beyond score accuracy: latency per conversation, API error rate, cost per scored conversation, percentage of conversations scored within SLA.

## 5. Where I Cut Corners on Purpose

| Shortcut | Why | What Production Looks Like |
|---|---|---|
| 200 conversations scored, not 10K | ~$3 and 30 min vs. ~$150 and 10+ hours. 200 (stratified by flow) is enough for credible distributions. | Async workers score 100% with aggressive caching |
| Pre-computed scores for demo | Can't wait 2s per conversation in a 10-min demo. Still demo live scoring via API to prove it works. | Real-time scoring with results cached |
| Uniform 0.80 threshold | Easy to explain, easy to read. The real answer is thresholds are a configuration decision, not an architecture decision. | Per-signal, per-customer thresholds set via calibration |
| LLM signals scored without anchored rubrics | Efficiency and Compliance define "good" concretely (baselines, action sequences). Resolution, Sentiment, and Communication define dimensions but not calibrated score levels — "0.5=partial" without examples of what "partial" looks like. Intentional: calibrating LLM judges requires annotated examples from the customer's QA team, not prototype defaults. | Few-shot rubrics with 2–3 annotated examples per score level per signal, tuned via calibration loop (kappa >0.7 target) |
| JSON file storage | No persistence layer needed for a prototype that resets between demos | Postgres or similar, with job queue for async scoring |
| No agent-level aggregation | ABCD dataset lacks agent IDs — can't demo what the data doesn't support | Core feature: per-agent dashboards, coaching workflows |
| Single API call per signal | One call with full conversation context vs. per-turn calls (30 turns x 3 signals = 90 calls). Loses real-time per-turn streaming, but this is batch review, not live monitoring. | Same for batch; per-turn for real-time use cases |
| No auth or multi-tenancy | Prototype is single-user, single-customer | OAuth + tenant isolation, customer-specific configs |
| Claude Sonnet, not Opus | Structured scoring tasks don't need Opus-level reasoning. 5x cheaper, 4x faster. At ASAPP's scale, this compounds. | Tiered: Haiku for screening, Sonnet for scoring, Opus for calibration edge cases |

## 6. What I'm Unsure About

**Whether the composite quality score is the right abstraction.** I use it as a sorting heuristic for the queue, but collapsing five dimensions into one weighted average loses important tensions. A conversation with 0.95 resolution and 0.30 compliance is very different from 0.60 across the board — but they might get similar composite scores. I'm not sure a weighted average is the right aggregation. It might be better to sort by "worst signal" or use the hard-block logic as the primary prioritization rather than a single number.

**Whether LLM-as-judge scales operationally across enterprise customers.** Each customer needs different rubrics, calibrated examples, and threshold configurations. That's a prompt management problem that multiplies across dozens of customers. Run-to-run variance is small (~±0.03), but model updates from Anthropic could shift scores across the board. Maintaining golden sets per customer per signal per rubric version is real operational overhead. I'm not sure the maintenance burden scales gracefully.

**Whether per-conversation scoring is the right unit without agent IDs.** The QA Manager coaches agents, not conversations. Without agent aggregation, this tool tells her "here are bad conversations" but not "here's who needs coaching." That agent-level view is what transforms a search tool into a coaching product. I'm unsure how much standalone value per-conversation review provides without it — it might only be useful as a stepping stone to the agent-level product.

---

*Built for the ASAPP Senior PM, Voice case study. Dataset: ABCD v1.1 (ASAPP Research). Stack: Python, FastAPI, Streamlit, Claude API.*
