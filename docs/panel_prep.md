# Interview Panel Prep — Case Study Presentation

---

## Panel Overview

| Name | Role | Represents | Primary Lens |
|------|------|-----------|-------------|
| **Farshad Samimi** | Director of Product (Voice + Agentic Core) | Product / Hiring Manager | Production-grade architecture, evaluation rigor, cost-efficiency |
| **Connor McNabb** | Senior Director, Product Design | Design | UX, information architecture, user journey, actionability |
| **Nimrod Broshy** | Director of PM (Supervisor Suite) | Product (adjacent team) | Outcome metrics, observability, supervisor workflows, feedback loops |
| **Brian King** | Senior Software Engineering Manager (Voice Infra) | Engineering | System architecture, scalability, voice domain, enterprise integration |
| **Gabe Maggiotti** | Director, ML Engineering | Engineering / Research | ML system design, LLM-as-judge, cost per eval, calibration, production ML |

---

## Farshad Samimi — Hiring Manager

**Background**: PhD Computer Science (Michigan State, distributed systems). Serial founder (Contract Wrangler, acquired by Conga). Writes extensively on voice AI architecture.

**His philosophy in his own words**: *"Vibes are not a strategy."* He benchmarks AI agents against live human performance across three dimensions: technical resilience, functional trust, and task efficiency. He wrote an entire blog post on the "demo-to-production gap" — how AI sounds impressive in demos but fails in production due to architectural weaknesses, not capability gaps.

**What he'll probe**:
- **Evaluation rigor**: How do you know the scores are accurate? He'll want to hear about calibration methodology (Cohen's kappa, inter-annotator agreement), not just "the LLM scores it." Be ready to explain the rubric embedded in each signal's prompt and how you'd validate it with human reviewers.
- **Production architecture**: He thinks in layers and systems. Show the separation of concerns (ingest → engine → API → dashboard). He'll appreciate that the API is the real product and the dashboard is one consumer.
- **Context engineering**: He wrote a piece arguing context management is a competitive advantage you own. He'll care about how you structured prompts and rubrics for the LLM judge — not just which model you picked.
- **Cost consciousness**: He'll test whether you understand ASAPP's "cost-efficient AI at scale" positioning. Have the tiered scoring cost table ready ($3/day at 1K vs $200/day at 100K).
- **The "natural vs. reliable" tradeoff**: For voice specifically, he sees tension between models that sound natural and models that follow instructions reliably. Analogize this to the LLM judge: the tradeoff between nuanced, context-aware scoring and deterministic, reproducible results.

**What to emphasize for him**:
- The tiered scoring architecture (heuristic on all, LLM on flagged + sample)
- Why Sonnet over Opus (cost/speed alignment with ASAPP philosophy)
- The single-API-call-per-signal design (3 calls per conversation, not 90)
- How you'd run a calibration sprint with a customer's QA team

**Likely hardest question**: *"Your LLM judge gives this conversation a 0.72 on compliance. A human reviewer gives it 0.45. Who's right, and what do you do about it?"*

---

## Connor McNabb — Design

**Background**: Senior Director of Product Design. Career arc from copywriting/branding (Huge agency) → fintech UX (Betterment) → enterprise AI UX (ASAPP). Named inventor on an ASAPP speech processing patent (stochastic future context). Gave a talk on "Design system APIs and the developer experience."

**What he'll evaluate**:
- **User journey, not feature list**: Walk through the QA Manager's morning. "She opens the dashboard at 7:30 AM, sees 8 hard blocks — that's 4 fewer than yesterday. She clicks Refund, lands on the 5 compliance-flagged conversations, reviews the first one..." This narrative is more compelling than "this page has KPI cards."
- **Information architecture**: Is the hierarchy right? Can you scan the Quality Summary in 5 seconds? Does the Review Queue's master-detail pattern feel familiar (email client UX)?
- **Actionability over analytics**: Every visualization should answer "What does the QA Manager do with this?" If it doesn't, justify why it's there or acknowledge it should move.
- **Language and labels**: He comes from copywriting. Signal names like "Biggest Gap" instead of "Min Signal Score" — he'll notice. Tooltips, empty states, error messages matter.
- **Design tradeoffs**: Why two views instead of three? Why disable the feedback button instead of omitting it? Why the radar chart?

**What to emphasize for him**:
- The persona-driven design principle ("Every feature must answer: What does the QA Manager do with this?")
- The master-detail navigation pattern (borrowed from email/ticketing tools the QA Manager already uses)
- The Key Insights TL;DR section — designed as the first thing the QA Manager reads
- What Went Wrong / What Went Well in two columns — mirrors the coaching conversation frame
- Items you chose NOT to build and why (scatter plot, histogram — acknowledged as less actionable for daily use)

**Likely hardest question**: *"If you had another week, what would you change about the UX? What would you remove?"*

---

## Nimrod Broshy — Adjacent Product Leader (Supervisor Suite)

**Background**: Director of PM at ASAPP, owns the Supervisor Suite. Previously VP Product at SundaySky (personalized video platform), started as an engineer at Intel in Israel. BSc from Ben-Gurion University. Authored ASAPP's Insights Agent launch and a blog post explicitly arguing that **containment rate is a flawed metric**.

**His published philosophy**: Goal Completion > Containment Rate. He uses the example of an AI agent confidently giving wrong baggage policy info — it "contains" the call (looks like success) but actually harms the customer. He advocates for multi-dimensional quality scoring across: goal achievement, accuracy, naturalness, friction, and escalation appropriateness.

**What he'll probe**:
- **Outcome-oriented metrics**: Your Resolution signal maps directly to his "Goal Completion" concept. He'll love this. Be ready to explain why Resolution gets the highest weight (0.30) and how it differs from mere "containment."
- **Observability and explainability**: Can the QA Manager see WHY a conversation scored low? He demands transparency into agent reasoning. Your evidence quotes, flagged utterances, and compliance checklists directly address this.
- **Feedback loops**: He wrote that guardrails must create feedback loops. He'll ask how the system improves over time. Talk about the calibration loop (human reviews → measure agreement → tune rubric), and how the disabled "Add Feedback" button becomes the anchor for that loop.
- **Scale of coverage**: His Insights Agent processes every conversation, not samples. He'll appreciate the tiered approach (heuristic on 100%, LLM on flagged + sample) — it's the same philosophy his product uses.
- **Actionability for supervisors**: His entire product org exists to help supervisors and QA managers act on insights. Your Review Queue with priority sorting, Key Insights TL;DR, and cross-view navigation directly serve his user.

**What to emphasize for him**:
- The 5 signals map almost 1:1 to his published quality framework
- The hybrid compliance signal (heuristic catches 80%, LLM handles nuance) — he'll see the parallel to his own products
- The "Talk About" strategy: human feedback, calibration, regression detection
- How cross-view navigation completes the insight-to-action loop

**Likely hardest question**: *"How do you handle the case where the LLM judge says the issue is resolved, but the customer calls back the next day with the same problem?"* (Goal Completion vs. apparent resolution)

---

## Brian King — Engineering (Voice Infrastructure)

**Background**: Senior Software Engineering Manager at ASAPP, leading voice infrastructure. Career arc: Avaya (10+ years, enterprise telephony/SIP) → Pindrop (voice fraud detection/authentication) → ASAPP (Solutions Architect → Staff → Engineering Manager → Senior Engineering Manager). Deep in FreeSWITCH, OpenSIPS, RTPengine, SIP, and the ASR → LLM → TTS pipeline.

**What he'll probe**:
- **System architecture**: He builds production infrastructure. He'll want to understand the data flow: How does a conversation get from the telephony system → transcript → scoring engine → API → dashboard? Your architecture diagram (ingest → engine → API → dashboard) should be clear.
- **Scalability**: He handles thousands of concurrent real-time audio streams. He'll ask: "What happens when we score 50K conversations/day?" Have the async engine with semaphore (max 5 concurrent), the tiered scoring approach, and the cost table ready.
- **Voice domain awareness**: Even though this is text-only, show you thought about voice. Your tradeoffs.md covers what changes for audio (dead air, talk-over ratio, prosody, ASR errors). Mention ASAPP's S2S models and how the quality signal framework stays the same — swap text-based signal computers for audio-based ones.
- **Integration architecture**: How would this plug into ASAPP's existing platform? The API-first design (FastAPI with clear contract) is the right answer. He'll appreciate that the dashboard is just one consumer.
- **Reliability and error handling**: The semaphore-controlled concurrency, incremental saving in seed_data.py, graceful degradation when LLM is unavailable (heuristic-only fallback) — these are production patterns he values.
- **Security**: Given his Pindrop background (voice fraud/authentication), he may ask about PII handling in transcripts, data retention, and access controls.

**What to emphasize for him**:
- API-first architecture (the API is the product, dashboard is a view)
- Async scoring engine with concurrency control
- Heuristic fallback when LLM is unavailable
- What changes for voice (handle time replaces turn count, prosody augments text sentiment, S2S opportunity)
- The pre-compute strategy for demo performance

**Likely hardest question**: *"Our telephony pipeline produces transcripts with ASR errors, speaker diarization issues, and missing turns. How does that affect your scoring reliability?"*

---

## Gabe Maggiotti — ML Engineering

**Background**: Director of ML Engineering at ASAPP, managing a team of ~22 ML engineers. Argentine (ITBA-educated). Career: MercadoLibre → Artear (media) → Jampp (ad-tech) → ASAPP. Published at NeurIPS WANT Workshop on DYAD (making Transformer layers 7-15% faster while maintaining 90%+ performance). Completed coursework at MIT (Quantum Physics), Georgia Tech (ML), and Stanford (Deep Learning). Active GitHub with 33 repos.

**His core belief**: Efficiency is everything. The DYAD paper is literally about making neural networks cheaper and faster without sacrificing quality. This maps directly to ASAPP's value proposition.

**What he'll probe**:
- **LLM-as-judge design**: He'll drill into the actual prompt design. How is the rubric structured? What's in the system prompt vs. user prompt? How do you enforce structured JSON output? How do you handle when the LLM returns malformed JSON?
- **Cost per evaluation**: He'll want the exact math. ~$0.015/conversation with Sonnet × 3 LLM signals. How that compares to Opus ($0.075) and Haiku ($0.005). Why you chose the middle tier.
- **Calibration methodology**: As a researcher, he understands that ML outputs need ground truth validation. He'll ask about inter-annotator agreement, how you'd measure LLM judge accuracy, and what happens when the LLM judge drifts over time.
- **Signal design choices**: Why these 5 signals and not others? Why separate sentiment trajectory from communication quality? Why is efficiency heuristic-only? He'll test the ML reasoning, not just the product reasoning.
- **Scaling the ML pipeline**: Batch processing, caching strategies, concurrent API calls, how you'd handle rate limiting at 50K conversations/day. The semaphore pattern and tiered approach will resonate.
- **Reproducibility**: Are the scores deterministic? What's the variance if you score the same conversation twice? (Answer: LLM scoring has inherent variance; in production you'd ensemble multiple runs or use temperature=0.)

**What to emphasize for him**:
- The hybrid compliance signal (heuristic for 80% of the work, LLM for the 20% that needs judgment)
- Single API call per signal (3 calls per conversation, not 90 per-turn calls)
- Structured output parsing with fallback error handling
- The tiered scoring model (heuristic on all → LLM on flagged + sample → deep analysis on-demand)
- Cost comparison table across model tiers
- How you'd run a calibration loop with human-labeled ground truth

**Likely hardest question**: *"Your sentiment signal uses a single LLM call to score all customer turns. How do you know it's not just averaging out the sentiment rather than capturing the trajectory? What if it hallucinates frustration spikes that aren't there?"*

---

## Cross-Panel Dynamics

### Who Will Likely Lead the Discussion
**Farshad** — as hiring manager, he sets the agenda and will ask the opening questions. He'll likely let each panelist drive their domain.

### Natural Alliances
- **Nimrod + Farshad** on evaluation rigor and production thinking — they're both product leaders who publish on measurement
- **Brian + Gabe** on technical architecture — they'll cross-validate engineering claims
- **Connor** stands alone on design but will amplify user empathy concerns that Nimrod raises

### Potential Tension Points
- **Gabe may push for more ML sophistication** (per-turn models, fine-tuned classifiers) while **Farshad will value pragmatic cost-efficiency**. Your tiered approach is the right answer for both.
- **Connor may question the Coaching Pattern Map scatter plot** (not actionable for daily use) while **Nimrod may defend it** (useful for supervisor insights). Know your position.
- **Brian may ask about voice features** that are out of scope. Don't get pulled into building voice — acknowledge it, reference tradeoffs.md, and redirect to the text prototype's strengths.

### The Meta-Question They're All Asking
Each panelist phrases it differently, but they're all evaluating the same thing:

> *"Does this person think like someone who has shipped production AI products to enterprise customers — or like someone who built a cool demo?"*

Your strongest signal: the **"Talk About, Don't Build"** strategy. It shows you know the difference between what impresses in a demo and what matters in production. Every panelist will recognize this as a sign of maturity.

---

## Quick Reference: What Each Person Will Appreciate Most

| Panelist | Strongest Card to Play |
|----------|----------------------|
| **Farshad** | "Vibes are not a strategy" — your calibration loop and cost-efficiency analysis |
| **Connor** | The QA Manager's morning journey — walkthrough the workflow, not features |
| **Nimrod** | Resolution = Goal Completion, not containment. The 5 signals map to his published framework |
| **Brian** | API-first design + what changes for voice. The architecture diagram |
| **Gabe** | The hybrid compliance signal + cost per eval math. Single call per signal, not per turn |
