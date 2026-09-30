# Panel Probes — Gaps, Twists & New Constraints

Probes that go beyond what's covered in `interview_prep.md`, surfaced from the deeper discussions during build. Organized by who's most likely to ask, with natural responses.

---

## Farshad (Hiring Manager / Product)

### P1: "You admitted your LLM rubrics are unanchored. How do you know the scores are even directionally correct?"

**Why he'd ask this**: You added "LLM signals scored without anchored rubrics" to the corners-cut table in tradeoffs_v2. He'll test whether you understand the implications of shipping scores that aren't validated.

**Response**: "I don't know for certain — and that's the honest answer. What I do know is that the scoring dimensions are grounded in what contact centers actually measure: did the issue get resolved, did the agent follow process, did sentiment improve or degrade. The scores are consistent within the prototype — the same type of conversation scores similarly — which means the rubric is at least internally coherent. But 'internally coherent' isn't the same as 'correct.' Correct requires human labels. That's why I call these scores directional in the dashboard — the prototype demonstrates the framework and the signal architecture, not calibrated ground truth. The first thing I'd do with a real customer is run a calibration sprint: their QA team scores 200 conversations, we measure agreement, and we anchor the rubrics with real examples of what a 0.3 vs a 0.8 looks like for their context."

---

### P2: "You talked about real-time guardrails as a natural extension. If you build that, does this batch reviewer become redundant?"

**Why he'd ask this**: He's testing whether you see these as competing products or complementary layers. ASAPP sells both real-time agent assist and post-call analytics.

**Response**: "They serve different decisions. Real-time guardrails prevent harm in the moment — block the agent from skipping identity verification, flag a compliance violation before it completes. But they can't tell you that refund calls have had a 15% compliance failure rate trending upward over three weeks. That's a systemic insight that only emerges from aggregate batch analysis. The QA Manager uses real-time guardrails to stop individual fires. They use batch review to find patterns, identify coaching targets, and escalate process changes. ASAPP already operates this way — CoachingAI does post-call QA, while their real-time agent assist handles in-the-moment guidance. These are complementary layers, not competing products."

---

### P3: "How do you handle prompt versioning? If you change a scoring prompt, how do you know what version produced which scores?"

**Why he'd ask this**: He's been at ASAPP long enough to know that prompt management at scale is a real operational headache. The prototype doesn't address this.

**Response**: "Right now, it doesn't — the prompts are hardcoded in the signal files. In production, I'd version prompts the same way you version code: each prompt gets a hash or semantic version, and every scored conversation records which prompt version produced its scores. When you update a prompt, you re-run the golden set against the new version before deploying. If scores shift, you know it's the prompt change, not model drift. The scoring result object would carry metadata — model version, prompt version, timestamp — so you can always trace back to exactly what produced a score. This is especially important when you're debugging disagreements between the LLM judge and human reviewers."

---

### P23: "This is a batch review tool. We have a streaming cascade. How does this integrate — or does it just sit alongside?"

**Why he'd ask this**: Farshad told you about ASAPP's streaming cascade architecture. He'll want to know you understood the implications and aren't just building something disconnected from their platform.

**Response**: "They're complementary layers, not competing products. The streaming cascade handles real-time decisions — block the agent from skipping identity verification, flag a compliance violation before the call ends, trigger a supervisor alert on escalation keywords. Those are in-the-moment interventions that prevent harm.

This tool handles batch post-call analysis — the stuff that only emerges from aggregate review. Things like: refund calls have had a 12 percent compliance failure rate trending upward over three weeks, or the new troubleshooting workflow is causing resolution failures in a specific subflow. Those are systemic insights that drive process changes, training programs, and knowledge base updates. You can't see those patterns in real-time.

The integration is straightforward. Conversations flow through the streaming cascade during the call. After the call ends, transcripts land in whatever data store ASAPP uses. The quality reviewer picks them up asynchronously — batch scoring on a schedule, or event-driven if you want scores within minutes of the call ending. Scores flow back into the Supervisor Suite or the customer's analytics layer.

The signals are actually reusable across both modes. Compliance action-sequence matching can run in real-time during the call as a guardrail, and the same logic can run post-call for the quality score. The LLM judgment layer is what's batch-only — it needs the full conversation context, which you only have after the call ends."

---

### P24: "You built this on text transcripts. We're investing heavily in speech-to-speech. Why didn't you address voice?"

**Why he'd ask this**: ASAPP's research team has a dedicated S2S effort. Farshad told you this explicitly. He wants to know you're thinking about where the company is headed, not just where the prototype is today.

**Response**: "Two reasons I didn't build it, and one reason I'm glad I didn't.

First, the case study provided text transcripts — the ABCD dataset is text. Building voice features on text data would have been dishonest. Second, voice signal processing — prosody analysis, dead air detection, diarization-aware sentiment — is a meaningful engineering effort that would have eaten the time I spent on the scoring framework and dashboard, which are where the product decisions live.

The reason I'm glad I didn't: the signal framework I built is deliberately modular. Each signal is a separate computer with a defined interface — takes a conversation in, returns a score with evidence and reasoning. To move from text to voice, you swap the signal computers, not the framework. Sentiment goes from text-only to text-plus-prosody. Efficiency goes from turn count to handle time, dead air, and hold time. Communication picks up filler words, speech rate, and interruption patterns. And you add a new signal that doesn't exist in text — interaction dynamics: talk-over ratio, response latency, silence gaps.

Where ASAPP's S2S models get really interesting is that they could score audio directly without transcription. That eliminates the ASR error layer that currently degrades every text-based signal. A customer says 'that's fine' sarcastically — the text transcript loses the sarcasm, but the audio preserves it. S2S-native scoring would catch that. I wrote about this in the tradeoffs note because I think it's one of the most compelling production extensions — and it's unique to ASAPP because you actually have the in-house models to do it."

---

### P25: "Our customers use CCaaS platforms — Amazon Connect, Genesys, Five9. How does this plug into that world?"

**Why he'd ask this**: Farshad specifically mentioned CCaaS integrations, SIP connections, and IVR routing as adjacent areas for this role. He's testing whether you understand the enterprise deployment context.

**Response**: "The quality reviewer's integration surface is the API — it consumes transcripts and produces scores. In a CCaaS world, the flow would be: a call comes in through Amazon Connect or Genesys, ASAPP's voice agent handles it through the streaming cascade, and when the call ends, the platform generates a transcript and metadata — call duration, queue time, transfer history, disposition codes.

That transcript, plus whatever metadata the CCaaS provides, is what flows into the quality reviewer. The scoring engine processes it, and the results go back to wherever the customer needs them — the ASAPP Supervisor Suite, the CCaaS's own analytics layer, or a BI tool like Looker or Tableau.

The key architectural decision is that the quality reviewer doesn't need to know about the telephony stack. It reads transcripts and writes scores. The SIP connections, IVR routing, agent assignment — all of that happens upstream. The scorer is downstream and decoupled. That's intentional because every enterprise customer has a different telephony setup, and the scorer shouldn't care.

What the scorer should care about is the metadata that comes with the transcript — things like queue time, number of transfers, and call reason from the IVR. Those enrich the scoring context. For example, if a customer waited 20 minutes in queue before reaching an agent, their sentiment baseline is already negative, and the scorer should account for that. The API contract I built already accepts conversation metadata alongside the transcript, so that integration point is ready."

---

### P26: "Did you actually test whether these signals correlate with quality? Or are you just assuming they do?"

**Why he'd ask this**: This is the Farshad pattern from your hiring manager interview — he pushed for "did you do any testing?" on voice cloning and "how did you test latency?" on vendor selection. He wants concrete evidence, not frameworks.

**Response**: "Let me be specific about what I did and didn't validate.

What I tested: I ran the scoring pipeline on 200 stratified conversations — about 20 per flow — and manually reviewed 30 of them to gut-check signal alignment. For compliance specifically, I compared the heuristic action-sequence scores against the ground truth in the ABCD knowledge base annotations. The heuristic correctly identified missing actions in all cases I checked — it's deterministic, so that's expected. For the LLM signals, I looked at the 10 most extreme cases — 5 highest and 5 lowest scores per signal — and verified that the reasoning and evidence matched my reading of the transcript. They were directionally correct in every case I checked.

What I didn't test: I didn't measure statistical correlation because I don't have external ground truth to correlate against. There's no CSAT data in the ABCD dataset, no human QA labels, no agent performance metrics. I also didn't measure inter-rater reliability because I'm one reviewer, not three.

What I would test in production, concretely: first, have three QA analysts independently score those 200 conversations on the same five signals. Measure Cohen's kappa per signal — target above 0.7 for inter-human agreement, and above 0.6 for LLM-versus-human. Second, correlate quality scores with CSAT surveys on the same conversations. If high-scoring conversations consistently get low CSAT, the framework is measuring the wrong thing. Third, track whether agents who get coached based on these scores actually improve on those signals in subsequent conversations. That's the ultimate validation — are the scores actionable?

I didn't want to fake validation. The honest answer is: the scores are directionally correct based on spot-checking, the framework is designed for rigorous calibration, and the calibration itself is a customer onboarding activity."

---

## Connor (Design)

### P4: "The trend column uses simulated prior-period data. What happens when a QA Manager sees a trend that contradicts what they see in their other tools?"

**Why he'd ask this**: He's a design lead — he'll spot that the trend data is synthetic and challenge the UX decision of showing fake trends.

**Response**: "Fair pushback. The trend column exists to demonstrate the feature pattern, not to show real data. In the prototype, I'm generating the prior period by adding noise to current scores — which means the trends are directionally meaningless. I chose to show it rather than hide it because the QA Manager's workflow depends on trend visibility — 'are we getting better or worse' is one of their daily questions. If I removed trends entirely, the dashboard would feel static and the panel wouldn't see how it fits the workflow. But you're right that showing synthetic trends risks the QA Manager trusting something that isn't real. The production answer is that trends only appear after two real scoring runs — the first run shows 'baseline established, no trend yet.' That's more honest and avoids the false-confidence problem."

---

### P5: "Your entire tier system is color-coded — green, yellow, red. What about color-blind users?"

**Why he'd ask this**: Accessibility is table-stakes for enterprise software. ASAPP's customers are Fortune 500 companies with accessibility requirements.

**Response**: "Good catch — the current implementation relies on emoji colors as the primary differentiator, which fails for red-green color blindness. The emoji plus text label helps — 'Above Bar' vs 'Below Bar' is readable regardless of color perception — but the scatter plot and histogram rely purely on color. In production, I'd add shape encoding to the scatter plot — circles for above bar, triangles for marginal, squares for below bar — and use patterns or hatching in the histogram alongside color. The tier system itself is sound; the visual encoding needs a second pass for accessibility compliance."

---

### P6: "You designed for a QA Manager. But who else in the org would want access to this, and how would the design change?"

**Why he'd ask this**: Testing whether you've thought about the product beyond a single persona.

**Response**: "Three other consumers, each with a different view. A team lead wants agent-level rollups — 'how is my team doing this week' — which the prototype can't show because the dataset lacks agent IDs, but the API already returns per-conversation scores that you'd aggregate by agent. An ops director wants cross-team comparisons and capacity planning — they care about volume and trends more than individual conversations. They'd use the Quality Summary view but at a higher aggregation level. And the training team wants the specific failure examples — 'show me five conversations where agents skipped the refund disclosure step' — which is essentially the Review Queue filtered to a specific failure mode. The data model supports all of these; the views are different lenses on the same scored conversations."

---

## Nimrod (Adjacent Product / Outcomes)

### P7: "What happens when your signals contradict each other? High resolution but low compliance — which one wins?"

**Why he'd ask this**: His published work focuses on outcome-oriented metrics. He'll probe whether the composite score papers over important tensions.

**Response**: "They shouldn't average out — that's the whole point of keeping them separate. The composite score is a convenient sort key for the queue, but the real insight is in the tension between signals. High resolution plus low compliance is the 'cowboy' pattern — the agent solved the problem but broke rules doing it. That's actually more dangerous than low resolution plus high compliance, because the customer is happy and nobody complains, but the company is exposed to regulatory risk. That's why the dashboard shows individual signal scores, not just the composite. The Failure Pattern Map visualizes exactly this tension — it plots resolution against compliance specifically to surface these archetypes. The composite score gets the conversation into the queue; the individual signals tell you what to do about it."

---

### P8: "Your resolution signal checks whether the issue was resolved in the conversation. But what if the customer calls back the next day with the same issue?"

**Why he'd ask this**: This is the false-positive problem — your LLM says resolved, reality says otherwise.

**Response**: "That's the gap between in-conversation resolution and actual resolution, and you can't close it from a single transcript. You need session linking — connecting a customer's conversations over time to detect repeat contacts. If the same customer calls about the same issue within 72 hours, the first conversation's resolution score should be retroactively downgraded. The prototype can't do this because the ABCD dataset doesn't have customer IDs or session history, but the scoring framework supports it — resolution becomes a two-pass signal: initial score from the transcript, adjusted score from follow-up data. This is also where CSAT correlation becomes critical. If conversations scored as resolved consistently correlate with repeat contacts, the resolution rubric is miscalibrated."

---

### P9: "If resolution and sentiment always move together, is one of them redundant?"

**Why he'd ask this**: Signal independence — are you measuring five things or really three things with different names?

**Response**: "They're correlated but not redundant — the interesting cases are precisely where they diverge. A customer can be satisfied but unresolved — 'thanks for trying, I'll figure it out myself.' That's high sentiment, low resolution, and it's a silent failure your CSAT survey won't catch because the customer was polite. Conversely, a customer can be frustrated throughout but fully resolved — 'this took way too long but at least it's fixed.' That's low sentiment, high resolution, and it tells you the process works but the experience is bad. If the signals always moved together, you'd be right to consolidate. In practice, the divergence cases are where the coaching opportunities live."

---

### P28: "Quality scoring is one piece. How does it feed into the broader product — agent training, workflow optimization, customer reporting?"

**Why he'd ask this**: Nimrod thinks in terms of outcomes and goal completion. He'll push on whether quality scoring is a standalone feature or part of a larger system that drives actual improvement.

**Response**: "Quality scoring on its own is a diagnostic tool — it tells you what's wrong. The value multiplier is what happens downstream.

Three feedback loops. First, coaching workflows. When the scorer identifies that an agent consistently scores low on compliance in refund calls, that's a specific coaching target. You pull the three worst conversations as examples, generate a coaching summary — 'you're skipping the refund eligibility check in 40 percent of cases' — and hand it to the team lead. In production with agent IDs, this becomes automated: the system generates weekly coaching briefs per agent, prioritized by signal and severity.

Second, workflow optimization. If the scorer shows that a specific subflow — say, 'return product' — has systematically low resolution scores across all agents, the problem isn't the agents. It's the workflow. Maybe the knowledge base is missing steps, or the tools don't support the action the customer needs. That insight goes to the product team or the process team, not the coaching team.

Third, customer reporting. Enterprise customers need to show their leadership that AI-handled conversations meet quality standards. The quality scorer produces the data for that report — 'this month, 94 percent of conversations met the quality bar, up from 89 percent, driven by improvements in refund handling compliance.' That's the kind of metric that renews contracts.

The quality scorer is the measurement layer. The coaching system, the workflow optimizer, and the reporting engine are the action layers. You need the measurement first before any of those action layers can function — which is exactly what this prototype demonstrates."

---

## Brian (Engineering)

### P10: "You use asyncio.gather with a semaphore of 5. What happens when an API call fails mid-batch? Does the whole conversation fail?"

**Why he'd ask this**: He's a staff engineer. He'll probe error handling, retries, and partial failure modes.

**Response**: "Right now, yes — if one signal fails, the conversation gets a partial result with the failed signal marked as an error. The other signals still return. I chose not to build retry logic for the prototype because it adds complexity without changing the demo. In production, I'd add exponential backoff with 2-3 retries per signal, a circuit breaker that trips if error rate exceeds 10% across the batch, and a dead-letter queue for conversations that fail after retries. The key design choice is that signals are independent — a sentiment failure shouldn't block resolution scoring. Partial results are valid and should still surface in the review queue, flagged as 'incomplete scoring — 3 of 5 signals available.'"

---

### P11: "The golden set catches regressions. But how do you version it? What happens when the rubric changes and half your golden set labels are now wrong?"

**Why he'd ask this**: Golden set maintenance is a real operational problem that most people hand-wave past.

**Response**: "This is the hardest part of maintaining an eval suite. When you change the rubric — say you redefine what 'partial resolution' means — some golden set labels become stale. You can't just re-label everything because that defeats the purpose of having human-verified ground truth. The approach I'd use is versioning the golden set alongside the rubric. When the rubric changes, you fork: the old golden set validates the old rubric, and you run a relabeling sprint on a subset to seed the new version. During the transition, you run both — the old set catches regressions in unchanged signals, and the new set validates the updated signal. Over time, the old version is retired. It's the same pattern as database migrations — you don't delete the old schema until the new one is validated."

---

### P12: "You said you'd use Haiku for screening, Sonnet for scoring, Opus for calibration. How do you ensure scores are consistent across models?"

**Why he'd ask this**: Multi-model pipelines introduce calibration challenges that aren't obvious.

**Response**: "You don't assume consistency — you measure it. Each model tier has a different role, so exact score agreement isn't the goal. Haiku's job is binary triage: does this conversation need full scoring, yes or no? You measure Haiku's precision and recall against Sonnet's full scoring — if Haiku misses too many flagged conversations, you widen its filter. Sonnet is the primary scorer, so it's what the golden set validates against. Opus only runs during calibration — when human and Sonnet disagree on a conversation, you run Opus to see if a more capable model agrees with the human or with Sonnet. Opus is the tiebreaker, not a primary scorer. The consistency contract is: Haiku's triage should capture 95%+ of what Sonnet would flag, and Sonnet's scores should agree with human labels within the tolerance band."

---

### P27: "We have MCPs, A2As, SDKs — a whole integrations ecosystem. How does quality scoring fit into that?"

**Why he'd ask this**: Farshad mentioned ASAPP's integration ecosystem explicitly — MCPs, A2As, SDKs. Brian owns engineering for this. He'll want to know you thought about how quality scoring plugs into the broader platform, not just as a standalone dashboard.

**Response**: "The quality scoring API is already a tool-callable endpoint — it takes a conversation ID and returns structured scores with evidence. In ASAPP's ecosystem, it becomes an MCP server that any agent or tool can invoke.

There are three integration patterns I'd see. First, the agent builder tools. When a customer is building or tuning a voice agent, they need to evaluate whether their changes improved quality. The quality scorer becomes a test harness — run 100 conversations through the new agent config, score them, compare against the previous version. That's CI/CD for voice agents, and the API contract already supports it.

Second, real-time routing. If you're running the quality scorer on recent conversations and you detect a pattern — compliance failures in a specific flow spiking this hour — that signal could feed back into the routing layer. Route those calls to senior agents, or flag them for supervisor monitoring in real time. The batch scorer identifies the pattern; the real-time system acts on it.

Third, the analytics platform. Quality scores are a data source alongside conversation metadata, CSAT, handle time, and disposition codes. They flow into ASAPP's analytics layer via the API, and customers consume them through whatever BI tools they already use. The API-first design means the scorer doesn't need to own the visualization — it provides data, and the existing analytics ecosystem presents it.

The MCP integration specifically is interesting because it means the quality scorer could be invoked by other AI agents in the platform — not just human users. An orchestration agent could score a conversation it just completed and decide whether to escalate based on the quality result."

---

## Gabe (ML Engineering)

### P13: "You validate golden set results using tier match plus tolerance band. What about scores near the tier boundary — 0.49 vs 0.51?"

**Why he'd ask this**: Boundary sensitivity is a classic ML evaluation problem. Your entire action system pivots on these thresholds.

**Response**: "Boundary cases are where the system is least reliable and most consequential — a score of 0.49 triggers mandatory review, 0.51 doesn't. Two approaches. First, add a confidence margin: conversations scoring within 0.05 of any tier boundary get flagged as 'borderline' regardless of which side they land on. The QA Manager sees them in the queue with a 'borderline' tag and makes the final call. Second, for the golden set specifically, boundary cases get stricter validation — if the human label is 0.49, the LLM must also land below 0.50, no tolerance band. The tier boundary is a decision point, so accuracy there matters more than accuracy at 0.85 where both sides of the tolerance band produce the same action."

---

### P14: "Why not fine-tune a smaller model instead of prompt-engineering Sonnet for every signal?"

**Why he'd ask this**: He's an ML engineer. Fine-tuning is the obvious scaling play that reduces per-call cost and latency.

**Response**: "Fine-tuning is the right long-term play, but wrong for this stage. Fine-tuning requires labeled training data — hundreds of scored conversations per signal with human-verified labels. I don't have that yet. The prompt-engineering approach lets me iterate on rubrics quickly without retraining, which matters when you're still figuring out what 'good' means for each customer. The progression I'd follow is: start with prompted Sonnet to establish the rubric through iteration with the QA team, accumulate human-verified labels through the calibration loop, and once you have enough labels with stable rubrics, fine-tune a smaller model — maybe Haiku-class — that reproduces Sonnet's scoring at a fraction of the cost. You fine-tune once the rubric stabilizes, not before. Otherwise you're baking in a rubric you'll change next month."

---

### P15: "How do you handle LLM hallucinations in scoring? The model confidently returns a 0.90 compliance score but the agent clearly violated policy."

**Why he'd ask this**: LLM reliability for structured evaluation is an active research area. He'll want to know you've thought about failure modes.

**Response**: "This is why compliance is hybrid, not pure LLM. The heuristic layer checks the action sequence against the expected flow from the knowledge base — did the agent perform the required steps in the right order? That's deterministic and can't hallucinate. The LLM adjusts by plus or minus 0.2 for justified deviations. So even if the LLM hallucinates that everything was fine, the heuristic anchor limits the damage — a conversation missing three required steps can't score above 0.7 regardless of what the LLM says. For the pure LLM signals — resolution and sentiment — the defense is the golden set. If the model consistently misses a type of failure, that pattern shows up in calibration and you either adjust the prompt or add explicit examples to the rubric. You can't prevent individual hallucinations, but you can detect systematic blind spots."

---

### P16: "Your sentiment signal returns per-turn scores in a single API call. How do you know the model isn't just anchoring on the last few turns and retroactively scoring the early turns?"

**Why he'd ask this**: Positional bias in LLMs is well-documented. This is a sophisticated probe.

**Response**: "I don't know for certain — and that's a real risk. LLMs exhibit recency bias, so the model might read a conversation that ends positively and retroactively soften its scoring of early turns that were clearly frustrated. Two mitigations. First, the prompt asks for per-turn scores with explicit reasoning per turn, which forces the model to commit to each assessment before seeing the resolution. But that's a prompting technique, not a guarantee. Second, you could validate by scoring turns in isolation — pass each turn individually and compare against the full-context per-turn scores. If early-turn scores shift dramatically depending on whether the model has seen the ending, you've confirmed positional bias and need to adjust — either by scoring turns in windows or by weighting the trajectory computation to discount early-turn scores from the full-context pass. This is exactly the kind of thing the golden set should test: include conversations where early turns are clearly negative but the ending is positive, and verify the model captures the trajectory, not just the outcome."

---

## ASAPP Product-Aware Probes (Could Come From Anyone Who Knows The Product)

### P29: "This looks a lot like our Conversation Explorer. What's different about what you built?"

**Why they'd ask this**: Nimrod owns Conversation Explorer. He knows your Review Queue is similar. He's testing whether you know their product and whether you can articulate what your prototype adds or demonstrates beyond what they already have.

**Response**: "You're right — the Review Queue is similar in spirit to Conversation Explorer. Both surface transcripts with quality signals alongside flagged interactions for supervisor review. I studied Conversation Explorer when researching ASAPP's product suite, and it influenced how I designed the review workflow.

What my prototype demonstrates is the signal framework layer underneath. Conversation Explorer shows what happened. The quality reviewer adds a structured evaluation layer — five calibratable signals with weighted scoring, evidence and reasoning per signal, and aggregate pattern detection across call reasons. It's less about the UI and more about the scoring engine: how you define 'good,' how you tier the evaluation for cost efficiency, and how you'd calibrate it with a customer's QA team.

If this were a real product, the quality scorer would feed INTO Conversation Explorer, not replace it. The scores become another data source in the Supervisor Suite — alongside transcripts, AI reasoning, and customer metadata. The value isn't the dashboard I built; it's the scoring framework and the decisions behind it."

---

### P30: "You mentioned the CXP flywheel. Where exactly does quality scoring fit in that lifecycle?"

**Why they'd ask this**: Farshad wrote the flywheel blog post. He's testing whether you actually understood it or just name-dropped it.

**Response**: "Quality scoring is the feedback signal that makes the flywheel actually spin. Let me map it.

The Discovery Agent identifies automation opportunities — it needs to know which conversation types have the worst quality so it can prioritize what to automate next. Quality scores feed that prioritization.

The Developer Agent builds workflows — when it creates a new flow, it needs a definition of 'good' to build against. The quality signal rubrics provide that definition.

The Simulation Agent stress-tests before deployment — it needs pass/fail criteria. The quality scorer provides those criteria: did the simulated conversation meet the compliance threshold, the resolution threshold, the sentiment threshold?

The Optimization Agent continuously improves — it needs to know what's degrading and where. The quality trend analysis and per-signal pattern detection surface exactly that. Your blog post's IMEI verification example — failure detected, fixed, verified — that verify step IS quality scoring.

And the Insights Agent mines conversation data for patterns — it needs structured quality signals to aggregate. That's what the quality scorer produces.

So the quality scorer doesn't sit in one place in the flywheel — it's the connective tissue. It defines what 'good' means, measures whether you're achieving it, surfaces where you're not, and provides the feedback signal that drives the next cycle of improvement."

---

### P31: "Devidas wrote about Empirical vs Experiential metrics for AI agent performance. How do your signals map to that?"

**Why they'd ask this**: Devidas Desai is Farshad's boss (SVP Product). His framework is the official ASAPP taxonomy. Someone on the panel may reference it to test your ASAPP homework.

**Response**: "I read Devidas's blog post — it's a really useful taxonomy. My signals span both categories.

On the Empirical side: Efficiency maps to his handle time and resolution time metrics. Compliance maps to error rate and guardrail adherence. Resolution maps to first-contact resolution and goal completion.

On the Experiential side: Sentiment maps to his CSAT predictor and sentiment drift concepts. Communication maps to his quality of experience and trust signal dimensions.

What my prototype doesn't cover from his framework: latency, confidence calibration, and learning velocity — those are platform health metrics that live in the infrastructure layer, not the conversation quality layer. In production, I'd add those as operational metrics alongside the five conversation quality signals. That's actually what Farshad describes in his 'Architecture of Trust' blog as the three evaluation dimensions — technical resilience, functional trust, and task efficiency. My five signals cover functional trust and task efficiency. The operational metrics cover technical resilience."

---

### P32: "CoachingAI has three pillars — Automatic Compliance, Topic Mastery, Tool Mastery. Your prototype covers compliance. What about the other two?"

**Why they'd ask this**: They want to see if you understand CoachingAI deeply, not just the tagline.

**Response**: "Good question. My signals map to all three, just under different names.

Automatic Compliance maps directly to my Compliance signal — the hybrid heuristic-plus-LLM approach that checks action sequences against the knowledge base and has the LLM evaluate justified deviations.

Topic Mastery — whether the agent understood the customer's issue and provided accurate information — maps to my Resolution signal. A conversation where the agent resolved the issue correctly demonstrates topic mastery. The evidence field in the resolution score shows specifically what the agent got right or wrong.

Tool Mastery — whether the agent used the right systems and tools in the right order — is actually embedded in my Compliance signal's heuristic layer. The action-sequence matching from kb.json checks exactly this: did the agent use 'search order,' 'validate purchase,' 'process refund' in the expected order? Tool mastery is compliance at the action level.

If I were building this at ASAPP, I'd probably split Tool Mastery out as its own signal rather than bundling it into compliance. The coaching action is different — 'you skipped the identity check' is a compliance issue, but 'you used the wrong search tool' is a training issue. Different coaching conversations."

---

## Cross-Panel Probes (Could Come From Anyone)

### P17: "How long does onboarding take for a new customer? What's the cold-start problem?"

**Why they'd ask this**: ASAPP sells to enterprises. Time-to-value matters. The calibration loop you describe sounds like it takes weeks.

**Response**: "Day one, you get value — the heuristic signals run immediately with zero calibration. Turn count efficiency, action sequence compliance checking, basic quality triage. Scores are directional but the queue prioritization works. The LLM signals start with generic rubrics — the same ones in this prototype — which are good enough to surface obvious failures. Calibration is a refinement process, not a prerequisite. In the first two weeks, you run the calibration sprint — QA team labels 200 conversations, you measure agreement, adjust rubrics. By week three, scores are tuned to that customer's standards. The cold-start problem is real but bounded: the framework works out of the box, calibration makes it accurate, and the longer you run it the better it gets because the golden set grows."

---

### P18: "What if agents learn to game the signals? They hit all the compliance checkboxes but the customer is still frustrated."

**Why they'd ask this**: Goodhart's Law — when a measure becomes a target, it ceases to be a good measure. Any panelist could raise this.

**Response**: "That's exactly why you need multiple signals that can't all be gamed simultaneously. An agent who games compliance by mechanically checking every box will likely hurt efficiency — the call takes longer — and may hurt sentiment — the customer feels processed, not helped. The signals create tension: you can't optimize all five by gaming one. The more subtle version of gaming is agents who are great at making the transcript look good — using the right words, following the script — while not actually solving the problem. That's where resolution and CSAT correlation become your check. If an agent's resolution scores are high but their customers keep calling back, the scores are being gamed and you need to adjust what 'resolved' means. The defense isn't building ungameable metrics — that's impossible. It's measuring from multiple angles so gaming one signal exposes itself through another."

---

### P19: "You mentioned regression detection — scores dropping 5 points from baseline. But what if a score drop is correct? Maybe a new policy made calls genuinely harder."

**Why they'd ask this**: Not all regressions are bugs. Some are real-world changes. This tests whether you blindly chase metrics.

**Response**: "Great distinction. A score drop is a signal, not a verdict. When regression detection fires, the first question isn't 'what broke in the pipeline' — it's 'what changed in the world.' Did a new policy roll out? Did call mix shift — more complex issues routing to the same team? Did a cohort of new agents start? The regression alert triggers an investigation, not an automatic fix. The QA Manager's job is to determine whether the drop reflects a real quality change — in which case you coach or retrain — or an environmental change — in which case you adjust the baseline. The system should surface the drop and provide context — 'compliance in Refund calls dropped 7 points, coinciding with the new return policy effective March 1' — so the human can make the judgment call."

---

### P20: "You keep saying 'in production I'd do X.' What's the one thing you'd change about the prototype right now if you had one more day?"

**Why they'd ask this**: Tests prioritization instinct. There's a right answer here — it should be something that improves the prototype's credibility, not a new feature.

**Response**: "I'd anchor the compliance rubric with concrete examples from the dataset. Right now, the LLM signals for resolution, sentiment, and communication define scoring dimensions but not calibrated levels — the model decides what a 0.5 looks like. Compliance is partially anchored through the heuristic action-sequence matching, but the LLM adjustment isn't. If I had one more day, I'd pull ten conversations that human reviewers would clearly score differently — five obvious passes, five obvious fails — and add them as few-shot examples in the compliance prompt. That turns one signal from 'directional' to 'grounded,' and it would make the demo scores more defensible when the panel drills into specific conversations."

---

### P21: "The composite quality score is a weighted average. Is a single number even meaningful when it combines things as different as compliance and sentiment?"

**Why they'd ask this**: The composite score is a design choice that could be challenged from product, design, or ML perspectives.

**Response**: "On its own, no — and I don't present it that way. The composite score serves one purpose: queue prioritization. It answers 'which conversation should I review first,' not 'how good was this conversation.' The moment you click into a conversation, you see individual signal scores, the radar chart, and the key insights — that's where the actionable information lives. I debated removing the composite entirely and sorting purely by worst individual signal, but the QA Manager's mental model expects a single quality number — it's what they're used to from existing QA scorecards. The composite gets them into the right conversation; the signal breakdown tells them what to do. If the composite ever becomes the thing people optimize against instead of a sorting heuristic, it's doing more harm than good."

---

### P22: "You designed this for text conversations. ASAPP's biggest growth area is voice. Walk me through what breaks when you switch to voice transcripts."

**Why they'd ask this**: Different from Q28 in interview_prep (which asks what changes for voice). This asks what specifically breaks — a harder, more concrete question.

**Response**: "Three things break. First, efficiency — turn count becomes meaningless for voice because a single 'turn' might be 30 seconds of explanation or 2 seconds of 'yes.' You need handle time, dead air detection, and hold time, which require audio signal processing, not text analysis. Second, compliance action-sequence matching — my heuristic checks for specific actions in the transcript like 'verify identity' or 'process refund.' In a voice transcript, those actions might be described differently depending on the ASR output, or they might not be explicitly stated at all — an agent might verify identity by asking the customer to confirm their date of birth without ever saying the word 'verify.' The heuristic needs to become more fuzzy or the compliance signal needs to lean harder on the LLM. Third, speaker diarization errors — if the ASR misattributes who said what, sentiment scores flip. The customer's frustration gets tagged as the agent's words. You'd need a confidence threshold on diarization before trusting per-speaker sentiment analysis."

---

*Generated from build conversations, interview transcript analysis (recruiter + hiring manager), and gap analysis against interview_prep.md, panel_prep.md, decisions.md, and tradeoffs_v2.md. P23-P28 specifically informed by Farshad's interview probing style (wants concrete specifics, challenges vague answers) and the ASAPP platform details he shared (streaming cascade, S2S research, CCaaS integrations, MCP/A2A/SDK ecosystem).*
