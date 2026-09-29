# Tradeoffs Note — Conversation Quality Reviewer

## 1. Speed vs. Depth: Tiered Scoring

**Choice**: Heuristic signals run on 100% of conversations; LLM signals run on a configurable sample.

**Why**: A single LLM-scored conversation takes ~2s and costs ~$0.015. At 10K conversations/day, that's $150/day for full coverage. Most contact centers have 50-100K conversations/day.

**Production approach**: Tier the scoring pipeline:
- **Tier 1 (all conversations)**: Heuristic signals only — efficiency, basic compliance sequence matching. Instant, zero cost. Flags outliers.
- **Tier 2 (flagged + sample)**: Full LLM scoring on flagged conversations + a random 10% sample. Catches nuanced issues while keeping costs manageable.
- **Tier 3 (on-demand)**: Deep analysis triggered by QA analysts reviewing specific conversations.

This mirrors how ASAPP likely already thinks about compute allocation in their cascade architecture — cheap models filter, expensive models refine.

## 2. Heuristic vs. Model-Based Signals

**Choice**: Efficiency is pure heuristic; Compliance is hybrid; Resolution, Sentiment, and Communication are LLM-based.

**Why the split matters**:
- Turn count and action sequences are *structural* — a language model adds no value over counting.
- Whether an agent actually resolved an issue requires *semantic understanding* — heuristics can't capture this.
- Compliance sits in between: action sequence matching catches 80% of violations, but justified deviations require judgment.

**Tradeoff**: Heuristics are deterministic and debuggable; LLMs are probabilistic and opaque. In regulated industries (airlines, insurance), explainability matters. The hybrid approach lets us say: "The rule caught the deviation, and the model confirmed it was (or wasn't) justified."

## 3. Per-Turn vs. Per-Conversation Scoring

**Choice**: Sentiment uses per-turn scoring; all others score at the conversation level.

**Why**: Sentiment *trajectory* is the signal — a customer who starts frustrated and ends satisfied is a different story than one who starts neutral and ends frustrated. Collapsing to a single score loses this. For resolution and compliance, the conversation-level outcome is what matters.

**What changes for voice**: Per-turn analysis becomes more valuable with audio features — detecting dead air (>3s silence), overlapping speech (interruptions), prosody shifts (rising frustration), and speech rate changes. These are inherently turn-level signals. In a voice pipeline, I'd add a dedicated "Interaction Dynamics" signal using audio features, scored per-turn.

## 4. What Changes for Voice/Audio

This prototype works on text transcripts. For ASAPP's voice product, additional signals become available:

| Text Signal | Voice Equivalent | What It Adds |
|---|---|---|
| Sentiment (text) | Sentiment (text + prosody) | Tone of voice detects frustration before words do |
| Efficiency (turn count) | Efficiency (handle time + dead air) | Dead air and hold time are the real cost drivers |
| Communication (clarity) | Communication (speech rate, filler words) | "Um", "uh", rapid speech = agent uncertainty |
| — (not available) | Interaction Dynamics | Interruptions, talk-over ratio, response latency |

**S2S model opportunity**: ASAPP's speech-to-speech models could score audio directly without transcription, eliminating ASR errors and capturing paralinguistic features. The quality reviewer's signal framework would stay the same — swap the text-based signal computers for audio-based ones.

## 5. Cost at Scale

| Scale | Heuristic Only | Full LLM (5 signals) | Tiered (recommended) |
|---|---|---|---|
| 1K convos/day | Free | ~$15/day | ~$3/day |
| 10K convos/day | Free | ~$150/day | ~$25/day |
| 100K convos/day | Free | ~$1,500/day | ~$200/day |

The tiered approach (heuristic on all, LLM on 10-15% + flagged) reduces cost by 85% while still catching the conversations that need human review.

**Further optimization**: Cache signal scores by conversation fingerprint. If the same agent handles similar issues repeatedly, many conversations will share signal patterns. Batch similar conversations for a single LLM call with structured output.

## 6. Evaluation & Calibration

**The hard problem**: How do you know the quality scores are accurate?

**Approach**:
1. **Ground truth from QA teams**: Sample 200 conversations, have 3 QA analysts score them independently on the same 5 signals. Measure inter-annotator agreement (Cohen's kappa). Use consensus scores as ground truth.
2. **Score-CSAT correlation**: If the reviewer scores a conversation highly but the customer gives a low CSAT, something is wrong. Track correlation over time.
3. **Calibration by customer**: Different customers have different standards. An airline's "compliance" bar is higher than a retailer's. Support per-customer signal weights and thresholds.
4. **Drift monitoring**: LLM scoring can drift as models are updated. Run the ground truth set through the pipeline monthly and alert on score distribution shifts.

---

*Built for the ASAPP Senior PM, Voice case study. Dataset: ABCD v1.1 (ASAPP Research). Stack: Python, FastAPI, Streamlit, Claude API.*
