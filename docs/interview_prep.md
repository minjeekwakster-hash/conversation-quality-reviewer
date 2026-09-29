# Interview Prep — Case Study Presentation

**Format**: 10 min intro + 10 min demo + 30 min discussion
**Panel**: Farshad (hiring mgr), Connor (design), Nimrod (product), Brian (eng), Gabe (ML eng)

---

## PART 1: PROTOTYPE WALKTHROUGH (10 minutes)

### Opening (1 min)

> "So the case study asked me to build a Conversation Quality Reviewer — ingest batch transcripts, compute quality signals, and surface the results through an API and dashboard.
>
> Before I open the prototype, I want to share the lens I used to build it. The first thing I did was define the user. I assumed a QA Manager at an airline contact center — someone like a JetBlue QA lead who spends most of her day manually sampling calls, coaching agents, and reporting quality trends to leadership. Today she reviews maybe 1 to 5 percent of conversations. The rest is a blind spot.
>
> So the question I kept asking myself for every feature was: what does the QA Manager actually do with this? If I couldn't answer that, I didn't build it. That filter shaped everything you're about to see."

**Why this opening works**: It signals persona-driven thinking (for Connor), outcome orientation (for Nimrod), and production discipline (for Farshad) — all before showing a single screen.

---

### Stop 1: Quality Summary — KPI Cards (2 min)

> "This is the Quality Summary view — the QA Manager's morning landing page. She opens this at 7:30 AM and needs to answer one question in 5 seconds: are we better or worse than yesterday?
>
> These four KPIs at the top give her that answer. Overall Quality is the weighted composite — 0.71 right now. Pass Rate tells her what percentage of conversations met the bar. Hard Blocks are the ones that require mandatory review — a resolution below 0.50 or a compliance below 0.50. And Needs Review is anything flagged but not a hard block.
>
> You'll notice each KPI has a green or red delta underneath. That's comparing the current period against the prior period. So if she's looking at the last 7 days, the delta shows the change from the 7 days before that. She can switch time ranges here in the sidebar — last 24 hours, last 7 days, last 30 days, or all time.
>
> I added the temporal dimension because without it, you have a microscope with no timeline. You can see exactly what's happening right now but you can't tell if it's getting better or worse. And that matters a lot for a QA Manager — if hard blocks are trending down after a training session, that's a signal the training worked."

**Decision to highlight if asked**: "I started without time-based filtering — the original prototype was a static snapshot. When I stress-tested it through the QA Manager's daily workflow, I realized she couldn't answer 'is this improving?' — which is half her job. So I added date ranges and trend deltas."

---

### Stop 2: Quality by Call Reason Table (2 min)

> "Below the KPIs is this table — quality broken down by call reason. This is where the QA Manager goes from 'how are we doing overall' to 'where specifically do we have problems.'
>
> She can sort by worst quality, most volume, best quality, or biggest decline. Biggest decline is the one I'd highlight — it surfaces the call types that are getting worse over the selected time period. So if refund conversations dropped 4 points this week, that jumps to the top.
>
> Each row shows the average quality score, how many conversations are in that bucket, and a trend arrow. The trend uses a small stability band — anything within plus or minus 2 points shows as stable, so we're not alarming her over noise.
>
> And this is something I'm proud of — she can click the 'Review' button on any row, and it takes her directly to the Review Queue, pre-filtered to that call type with the relevant signal flags. So the workflow is: see the problem in the summary, click through, and land on the specific conversations that need attention."

**Decision to highlight if asked**: "I chose call reason as the primary drill-down axis because quality issues are almost always specific to a workflow, not universal. An airline might have great performance on flight status but struggling on refunds. That specificity is what lets the QA Manager take action — she can tell training to focus on refund handling, not just 'be better.'"

---

### Stop 3: Signal Breakdown & Supporting Visuals (1 min)

> "Below the table, there's a horizontal bar chart showing average scores across the five signals — Resolution, Compliance, Efficiency, Sentiment, and Communication. This helps the QA Manager see which dimension is the weakest across the board.
>
> I also included a score distribution histogram and a coaching pattern map — the scatter plot of efficiency versus quality. I'll be honest — I debated whether these belong here. The histogram and scatter plot are more analytical than actionable. A QA Manager doesn't look at a scatter plot at 7:30 in the morning. But they're useful for a weekly review or when she's building a case for leadership. If I had another week, I'd probably move them to a separate analytics view and keep the main page focused on the table and KPIs."

**Why this candor works**: It shows design maturity — knowing what to build, what not to build, and being honest about where the line is. Connor will appreciate this. Farshad will see it as production thinking.

---

### Stop 4: Review Queue — Master-Detail (3 min)

> "Now let me switch to the Review Queue. This is where the QA Manager actually does her work.
>
> The left panel is a sorted list of conversations — hard blocks first, then flagged, then everything else. She can search by conversation ID or filter by signal type. If she clicked through from the summary table, the filters are already set.
>
> When she clicks a conversation, the right panel shows the detail. Let me walk through what she sees.
>
> First is the Key Insights section — this is the TL;DR. Two or three sentences that summarize what happened and what went wrong. I designed this as the first thing she reads because her next decision is 'do I need to dig deeper or can I move on?' If the summary tells her enough, she saves time. If not, everything below gives her the full picture.
>
> Below that is the score card — all five signals with their individual scores and the overall composite. There's a radar chart next to it that gives a visual shape of the conversation's quality profile.
>
> Then two columns: What Needs Improvement and What Went Well. I structured it this way because it mirrors how a coaching conversation works. When the QA Manager sits down with an agent, she doesn't just say 'you scored 0.6.' She says 'here's what you did well, and here's what needs work.' The dashboard sets up that conversation.
>
> Below that, for compliance specifically, there's an expandable section showing which actions were expected, which were taken, and which were missed. So if the agent skipped identity verification, it shows up right here — the QA Manager doesn't have to guess why compliance scored low.
>
> Then the sentiment trajectory chart — customer sentiment turn by turn. A line going up means the agent recovered the situation. A line going down is a warning sign. And at the bottom is the full annotated transcript with flagged utterances highlighted."

**Decision to highlight if asked**: "The master-detail layout is borrowed from email clients and ticketing tools — something the QA Manager already uses every day. I didn't want her to learn a new interaction pattern. Click on the left, details on the right, move to the next one."

---

### Stop 5: Architecture & Tradeoffs (1 min)

> "Under the hood, the architecture is straightforward. Conversations come in, go through an ingest layer, hit a scoring engine that runs five signal computers, and the results are served through a FastAPI API. The dashboard is just one consumer of that API — a customer could build their own integration, pipe scores into their existing tools, whatever works for them.
>
> One design choice I want to highlight: I use three LLM calls per conversation, not ninety. Instead of scoring each turn individually, each signal gets a single call with the full conversation context. That's a deliberate cost decision — at scale, the difference between 3 and 90 API calls per conversation is the difference between viable and not viable.
>
> And I tier the scoring: heuristics run on every conversation for free — turn count, action sequence matching. LLM scoring only runs on flagged conversations plus a random sample. At 100K conversations a day, that's about $200 a day instead of $1,500."

**Decision to highlight if asked**: "The API is the real product. The dashboard is a view. That matters because enterprise customers — especially airlines and telecoms — have their own dashboards, their own BI tools. If the quality reviewer is locked behind one UI, it's not useful. The API-first design means it fits wherever the customer already works."

---

### Closing the Demo (30 sec)

> "That's the prototype. Let me quickly mention what I chose not to build but would want to talk about — human feedback and calibration loops, agent-level aggregation and coaching workflows, regression detection over time, and how this changes when you move from text to voice. Happy to dig into any of these."

---

## PART 2: DISCUSSION PREP (30 minutes)

### How to Use This Section

Questions are organized by topic, not by panelist — because in a 5-person panel, anyone can ask anything. Each question lists the most likely asker(s) and a natural-sounding answer script. The scripts are written in first person, ready to speak aloud.

---

### TOPIC 1: EVALUATION RIGOR & CALIBRATION

**Q1: "How do you know the scores are accurate? What if the LLM judge is just confidently wrong?"**
*Likely from: Farshad, Gabe*

> "That's the hard problem, right? The LLM gives you a score with a confidence you didn't ask for. So the way I'd approach it in production — and this is actually what I did at Mudflap when we were building our eval system for voice AI — is you start with human ground truth.
>
> I'd take 200 conversations, have three QA analysts score them independently on the same five signals, and measure their agreement using Cohen's kappa. That gives you two things: a ground truth set you trust, and a baseline for how consistent human reviewers are with each other. Because here's the thing — humans don't agree perfectly either. If your human reviewers only agree 70% of the time, you can't hold the LLM judge to 95%.
>
> Then you score those same 200 conversations with the LLM and compare. Where the LLM disagrees with the human consensus, you look at the rubric. Is the rubric ambiguous? Did the LLM weigh something differently? That's your calibration loop — it's not a one-time thing, it's ongoing.
>
> At Mudflap, we built something similar. We had a golden set of 50-plus annotated transcripts that we'd run through the pipeline whenever we changed the prompts or upgraded the model. If scores shifted more than 5 points on the golden set, that was a gate — we'd stop and investigate before rolling anything out."

---

**Q2: "Your LLM judge gives this conversation a 0.72 on compliance. A human reviewer gives it 0.45. Who's right, and what do you do about it?"**
*Likely from: Farshad*

> "Neither is automatically right — that gap is a signal, not an answer. The first thing I'd do is look at the evidence. The compliance signal includes which actions were expected, which were taken, and which were missed. I'd pull that up and compare it to what the human reviewer flagged.
>
> Usually the disagreement falls into one of three buckets. First, the rubric is ambiguous — the human interpreted 'identity verification' as needing both name and account number, while the LLM counted just the name. That's a rubric fix, not a model fix. Second, the LLM is using context the human didn't — maybe the agent verified identity earlier in a transferred call, and the LLM saw that context while the human reviewer started from a later point. Third, the LLM genuinely got it wrong — it hallucinated an action that didn't happen.
>
> In each case the response is different, but the process is the same: pull the evidence, understand the gap, and either fix the rubric, add context to the prompt, or flag it as a known failure mode. And then that conversation goes into your golden set so you catch the same type of error in the future."

---

**Q3: "Are the scores deterministic? What's the variance if you score the same conversation twice?"**
*Likely from: Gabe*

> "They're not — and that's a real consideration. LLM scoring has inherent variance. Even at temperature zero, the output isn't perfectly deterministic across different API calls. In my testing, I see maybe plus or minus 0.03 to 0.05 on a given score.
>
> For a prototype, that's fine. For production, you have a few options. You could ensemble — score the same conversation two or three times and take the median. That increases cost but dramatically reduces variance. You could also use temperature zero consistently and accept the small remaining variance as noise, which is what I'd recommend starting with because the variance is usually smaller than the disagreement between human reviewers anyway.
>
> The bigger concern isn't run-to-run variance — it's drift over time. If Anthropic updates the model and sentiment scores shift by 0.1 across the board, that's a problem. That's where the golden set comes in. You run your reference conversations through the pipeline monthly and alert if the distribution shifts."

---

**Q4: "How do you handle the case where the LLM says the issue was resolved, but the customer calls back the next day with the same problem?"**
*Likely from: Nimrod*

> "That's exactly the difference between apparent resolution and actual resolution, right? And it's why I named the signal 'Resolution' and not 'Containment.' Containment just means the call ended without a transfer — that's a vanity metric. Resolution means the customer's problem was actually solved.
>
> Now, with a single conversation in isolation, the best the LLM can do is assess whether the resolution actions taken were appropriate and complete. It can't know if the customer calls back tomorrow. That's a data integration problem, not a scoring problem.
>
> In production, I'd want to join the quality score with downstream data — did this customer call back within 48 hours about the same issue? If they did, that's a retroactive signal that resolution was over-scored. Over time, that feedback loop teaches you which patterns of 'apparent resolution' are actually durable and which ones aren't.
>
> At Mudflap, we had a similar problem with our voice AI. The bot would complete a call and mark it as successful, but the driver would call back the next day. We started tracking repeat contacts within a 72-hour window and used that as a correction signal for our quality scores. It changed what we optimized for."

---

### TOPIC 2: SIGNAL DESIGN & ML CHOICES

**Q5: "Why these five signals and not others? Why not agent knowledge accuracy, or handle time, or customer effort?"**
*Likely from: Gabe, Nimrod*

> "I started by asking what the QA Manager actually coaches on. When I looked at how quality evaluation works in contact centers, it almost always breaks down into: did you solve the problem, did you follow the rules, were you efficient, how did the customer feel, and how well did you communicate. Those are the five.
>
> I could have added more — agent knowledge accuracy, customer effort score, escalation appropriateness. But more signals doesn't mean better. Each signal you add is another thing the QA Manager has to understand, trust, and act on. Five is already a lot. I'd rather have five well-calibrated signals than eight where three are mediocre.
>
> If I were building this at ASAPP, the specific signals might shift based on what the customer cares about. An airline might weight compliance way higher than a retailer because of regulatory requirements. A telecom might want a dedicated 'upsell appropriateness' signal. The framework is designed to be extensible — you can add or swap signal computers without changing the architecture."

---

**Q6: "Why is efficiency heuristic-only? Couldn't the LLM add nuance?"**
*Likely from: Gabe*

> "Turn count and action sequences are structural — you can count them. A language model adds no value over counting. And the cost of calling the LLM for something you can compute deterministically in milliseconds doesn't make sense, especially at scale.
>
> That said, 'efficiency' means different things in different contexts. For text, turn count relative to the expected flow length is a reasonable proxy. For voice, it's handle time, dead air, and hold time — those are the real cost drivers. The heuristic approach actually makes it easier to swap the metric by channel because you're not retraining or re-prompting anything."

---

**Q7: "The sentiment signal uses a single LLM call to score all customer turns. How do you know it's not just averaging the sentiment rather than capturing the trajectory?"**
*Likely from: Gabe*

> "Good question. The prompt explicitly asks for per-turn scores, not an average. It returns a JSON array with a sentiment score for each customer turn, and then I compute the trajectory from that — was it improving, declining, or flat.
>
> The risk you're pointing to is real though — the LLM could anchor on the overall tone and project it backward, or it could hallucinate a frustration spike that isn't there. The check is the evidence field. Each per-turn score comes with a quote from the transcript that the LLM used to justify the score. In the dashboard, the QA Manager can see the trajectory chart alongside the transcript and verify whether the scores match the conversation.
>
> In production, you'd validate this by pulling the 20 conversations with the steepest sentiment drops, having a human reviewer check the transcripts, and measuring agreement. If the LLM is hallucinating spikes, that shows up fast."

---

**Q8: "Why Claude Sonnet instead of Opus or Haiku? Walk me through that decision."**
*Likely from: Gabe, Farshad*

> "It's a cost-quality tradeoff that maps to ASAPP's positioning. Opus is the most capable, but at about five times the cost per call. For scoring quality signals — where the rubric is well-defined and the task is structured — Sonnet gives you 90-plus percent of the quality at a fifth of the price. Haiku is even cheaper, but in my testing the reasoning wasn't reliable enough for nuanced signals like resolution and compliance.
>
> The math: Sonnet costs about a cent and a half per conversation for three LLM signals. Opus would be about 7.5 cents. At 10K conversations a day, that's $150 versus $750. And with the tiered approach — heuristic on everything, LLM on maybe 15 percent — Sonnet brings it down to about $25 a day.
>
> ASAPP builds cost-efficient AI at scale. Picking the most expensive model and running it on everything would be the opposite of that philosophy."

---

### TOPIC 3: ARCHITECTURE & SCALE

**Q9: "What happens when a customer wants to score 50K conversations a day? Walk me through the scaling story."**
*Likely from: Brian, Farshad*

> "The tiered architecture handles this. At 50K conversations, you don't need to LLM-score all of them. Heuristics run on all 50K — turn count, action sequence matching — and that's instant, basically free. That first pass flags maybe 10 to 15 percent as needing deeper analysis, plus you take a random sample. So you're LLM-scoring maybe 7 to 10K conversations.
>
> For the LLM scoring, the engine uses async processing with a concurrency limiter — right now set to 5 concurrent API calls. In production you'd tune that based on rate limits and throughput targets. You'd also batch conversations — instead of processing them one at a time, you'd queue them and process in parallel with back-pressure.
>
> There's also a caching opportunity. If the same agent handles the same type of issue repeatedly, many of those conversations will look structurally similar. You could cache scoring results by conversation fingerprint and only score truly novel patterns.
>
> The cost at 50K with the tiered approach is about $125 a day. That's well within what an enterprise customer would pay for automated quality coverage on 100 percent of their conversations."

---

**Q10: "How would this plug into ASAPP's existing platform?"**
*Likely from: Brian*

> "The API is the integration surface. The dashboard is just one consumer — it hits the same endpoints any other system would. A customer could pipe the quality scores into their existing BI tool, their workforce management system, or their own internal dashboards.
>
> The API contract is clean — you send conversation IDs, you get back structured scores with evidence and reasoning. It's a FastAPI service with well-defined request and response models. In ASAPP's world, this would sit alongside the existing conversation pipeline — conversations come in through telephony, get transcribed, and the quality scorer processes them asynchronously. The scores land in whatever data store ASAPP uses and flow into the Supervisor Suite or whatever customer-facing surface makes sense.
>
> One thing I was intentional about: the quality reviewer doesn't own the conversation data. It reads transcripts and writes scores. It doesn't need to know about the telephony stack, the ASR pipeline, or the agent routing. That separation means it can plug in without disrupting anything."

---

**Q11: "Our telephony pipeline produces transcripts with ASR errors, speaker diarization issues, and missing turns. How does that affect your scoring reliability?"**
*Likely from: Brian*

> "It degrades it, and you have to be honest about that. If the transcript says the agent said something they didn't actually say because of an ASR error, the compliance and resolution scores can be wrong. If speaker diarization is off, the sentiment trajectory could attribute customer frustration to the agent or vice versa.
>
> The mitigations are at different layers. At the transcript layer, you can include ASR confidence scores alongside the text. Turns with low confidence get flagged, and the scorer can weight those turns lower or skip them for sentiment analysis. For diarization errors, you'd want to validate speaker labels against the telephony metadata — who was the caller versus the agent.
>
> At the scoring layer, the signal rubrics can be made more forgiving for noisy transcripts. Instead of penalizing an agent for not saying a specific compliance phrase, you look for semantic equivalents — did they verify identity in any form, even if the exact words are garbled.
>
> And this is where ASAPP's speech-to-speech models become really interesting. If you can score directly from audio instead of going through ASR, you eliminate the transcription error layer entirely. The signal framework stays the same — you just swap text-based signal computers for audio-based ones."

---

**Q12: "What about PII handling? These transcripts have customer names, account numbers, credit card info."**
*Likely from: Brian*

> "For the prototype, the dataset is synthetic — ABCD is generated data, so there's no real PII. But in production, this is critical, especially in regulated industries.
>
> The approach I'd take: PII should be masked or tokenized before it hits the scoring engine. The quality scorer doesn't need to know the customer's actual credit card number to evaluate whether the agent handled PCI compliance correctly — it just needs to know that a payment action occurred. The transcript that flows into the LLM should have PII redacted.
>
> ASAPP likely already has PII handling infrastructure for their existing products. The quality reviewer would plug into that same pipeline — PII gets stripped upstream, and the scorer only sees sanitized transcripts."

---

### TOPIC 4: UX & DESIGN DECISIONS

**Q13: "Walk me through the QA Manager's morning. What's her first 10 minutes look like?"**
*Likely from: Connor*

> "She opens the dashboard around 7:30. First thing she sees is the four KPIs with their deltas. Today's showing 8 hard blocks — that's 4 fewer than last week, so the training she ran on refund handling is working. Overall quality is at 0.71, up 2 points. Good.
>
> She scrolls to the call reason table, sorts by biggest decline, and sees that 'shipping status' calls dropped 5 points over the past 7 days. That's new — she clicks 'Review' on that row.
>
> Now she's in the Review Queue, filtered to shipping status conversations with the relevant flags. The first conversation is a hard block — compliance scored 0.38. She clicks it, reads the Key Insights: 'Agent provided incorrect shipping timeline without checking the order system first.' She opens the compliance detail — the agent skipped the 'search order details' step that should have happened before giving a status update.
>
> Now she has what she needs. She can pull this as a coaching example, share the insight with the training team that shipping status procedures need a refresher, and move to the next conversation. That whole loop — from 'something is off' to 'here's specifically what happened and what to do about it' — is maybe 3 minutes."

---

**Q14: "If you had another week, what would you change about the UX? What would you remove?"**
*Likely from: Connor*

> "Honestly, I'd remove more than I'd add. The scatter plot — the coaching pattern map — I'd pull out of the main view. It's interesting for a quarterly review but the QA Manager doesn't need it at 7:30 AM. Same with the score distribution histogram. They're not actionable enough for daily use.
>
> What I'd add: first, I'd redesign the coaching pattern into an agent-level view where you can see individual agents' performance over time. Right now the dataset doesn't have agent IDs so I couldn't build it, but that's where the real coaching value lives. Second, I'd add the feedback loop — a way for the QA Manager to say 'I disagree with this score, here's what I think it should be.' Right now there's a disabled feedback button that's a placeholder for that. Third, I'd add a simple export — let her generate a weekly summary report she can send to leadership without leaving the dashboard.
>
> The principle is the same: every feature has to answer 'what does the QA Manager do with this?' If it doesn't answer that question clearly, it moves to a secondary view or it doesn't get built."

---

**Q15: "Why two views instead of three? Why not a separate analytics view?"**
*Likely from: Connor*

> "I actually started with three views — Summary, Queue, and an API reference panel. The API reference was nice for the demo but useless for the QA Manager. So I moved it to the sidebar as a collapsed section.
>
> Two views maps to two modes of work: scanning and reviewing. The Summary is for scanning — am I okay, where are the problems. The Queue is for reviewing — let me look at specific conversations and decide what to do. Those are the two things the QA Manager does every day.
>
> A third analytics view could make sense later — for things like the scatter plot, score distributions, signal correlations, trend analysis over longer periods. But for an MVP, two views keeps it simple and learnable. The QA Manager shouldn't need a tutorial."

---

**Q16: "Why the radar chart? Isn't that generally considered bad data viz practice?"**
*Likely from: Connor*

> "You're right that radar charts get criticized — they can be misleading when axes have different scales, and they're hard to compare across multiple items. I chose it here for one specific purpose: giving a quick visual shape of the conversation's quality profile. Five signals, one shape. A balanced pentagon means the conversation was consistently good or bad. A lopsided shape immediately shows which dimension is the outlier.
>
> But I'd own that it's debatable. If the QA Manager doesn't find it useful in practice, I'd replace it with a simple horizontal bar chart of the five signal scores. The important thing is that the individual signal scores are also shown as numbers right next to it, so the radar chart is supplementary, not primary."

---

### TOPIC 5: HYBRID COMPLIANCE & SIGNAL ARCHITECTURE

**Q17: "Tell me more about the hybrid compliance signal. How does the heuristic and LLM work together?"**
*Likely from: Gabe, Nimrod*

> "Compliance has two components. The heuristic layer checks action sequences — for a given flow type, like 'refund,' there's a set of expected actions in a specific order: verify identity, search order, confirm eligibility, process refund. The heuristic checks which of those happened and whether they happened in the right order, and gives a base score.
>
> The LLM layer then applies a small adjustment — up to plus or minus 0.2 — based on context the heuristic can't see. For example, if the agent skipped identity verification, the heuristic flags that as a violation. But maybe the customer was already verified earlier in a transferred call, and the agent reasonably didn't re-verify. The LLM reads the conversation context and decides whether the deviation was justified.
>
> The heuristic catches about 80 percent of real compliance issues — the clear-cut ones. The LLM handles the 20 percent that requires judgment. And critically, the final score shows both layers — the QA Manager can see the heuristic score, the LLM adjustment, and the reasoning. It's not a black box."

---

### TOPIC 6: PRODUCTION THINKING & "TALK ABOUT, DON'T BUILD"

**Q18: "What would you build next if this were a real product?"**
*Likely from: Farshad, Nimrod*

> "Three things, in order.
>
> First, the human feedback loop. That disabled 'Add Feedback' button isn't decoration — it's the anchor for the most important feature the product needs. When the QA Manager disagrees with a score, she should be able to correct it. Those corrections become training data for calibration. Over time, you measure LLM-vs-human agreement and tune the rubrics based on where they disagree. Without that loop, the system doesn't improve.
>
> Second, agent-level aggregation. Right now this is conversation-level — you see individual conversations. But the QA Manager coaches agents, not conversations. She needs to see: 'Agent Sarah averages 0.82 overall but 0.55 on compliance in refund calls.' That's a specific, actionable coaching target. The dataset I used didn't have agent IDs, so I couldn't build this, but the data model supports it — you'd add an agent identifier to each conversation result and aggregate up.
>
> Third, regression detection. When you push a new prompt, change a model, or update a compliance rubric, scores shift. You need to know whether they shifted intentionally or broke something. That's a monitoring problem — track score distributions over time and alert on unexpected changes.
>
> At Mudflap, we learned this the hard way. We built our voice AI eval system in phases, and the biggest unlock wasn't the initial scoring — it was the feedback loop. When our QA team could flag issues and we could see them the next day in the metrics, the iteration speed went from weeks to hours."

---

**Q19: "How does this change for voice? What's different when you move from text to audio?"**
*Likely from: Brian, Farshad*

> "The signal framework stays the same — you're still measuring resolution, compliance, efficiency, sentiment, and communication. What changes is the inputs and what you can detect.
>
> Efficiency shifts from turn count to handle time, dead air, and hold time. Those are the real cost drivers — an extra turn in text is milliseconds, but 30 seconds of dead air in a phone call is 30 seconds of customer frustration.
>
> Sentiment gets way more interesting with audio. Tone of voice detects frustration before words do. A customer can say 'that's fine' in a way that clearly means it's not fine. Prosody, speech rate, volume changes — those are signals text can't capture.
>
> Communication quality gets filler words and speech patterns — excessive 'ums,' rapid speech when the agent is uncertain, interruptions and talk-over ratio.
>
> And then there's an entirely new signal that doesn't exist in text: interaction dynamics. Who's talking over whom, how long is the response latency, is there dead air where the agent is looking something up. That's inherently audio-based.
>
> ASAPP's S2S models are the really interesting opportunity here. If you can score directly from audio without going through ASR, you skip the transcription error layer entirely and you get paralinguistic features for free."

---

**Q20: "You mentioned you've built voice AI before. Tell me about that."**
*Likely from: Farshad*

> "At Mudflap — it's a fuel marketplace for truckers — I built our voice AI platform from zero. We started with outbound calls to fuel stations to negotiate pricing. The first version was rough — 60 percent hang-up rate. Stations would pick up, hear a bot, and hang up.
>
> We iterated fast. Voice cloning with Cartesia so it sounded natural instead of robotic. Better context engineering so the bot could handle objections and questions about the program. Prompt versioning so we could A/B test different approaches. Within a few months, hang-up rate dropped to about 10 percent, and we were running 18 percent conversion on connected calls.
>
> The eval system was the thing I'm most proud of. We built a two-layer evaluation framework — platform health metrics like connection rate and latency, and agent quality metrics across 13 dimensions including task completion, objection handling, and information accuracy. We set up a four-stage deployment pipeline: test, staging, pre-prod, production. Each stage had gates — if quality dropped below the threshold on the golden set, the deployment stopped.
>
> By the end, we were driving about $2.5 million in annualized GMV through the voice channel with zero incremental headcount. The voice AI handled the negotiation calls that sales reps didn't have time for."

---

**Q21: "What did you learn about evaluating AI quality that informed how you built this case study?"**
*Likely from: Farshad, Gabe*

> "A few things carried over directly.
>
> First, you need both layers — platform health and output quality. At Mudflap, we had metrics like connection rate and latency that told us the system was working, and then quality metrics like task completion and accuracy that told us the AI was doing a good job. In this case study, the heuristic signals are like platform health — structural checks that are fast and deterministic — and the LLM signals are like output quality — they require judgment.
>
> Second, golden sets are non-negotiable. We maintained 50-plus annotated transcripts that we ran through the pipeline on every change. If scores shifted more than 5 points, the deployment stopped. That same approach maps directly to how I'd calibrate the LLM judge here.
>
> Third, the hardest part isn't scoring — it's getting people to trust the scores. At Mudflap, the QA team initially didn't trust the automated evals. What won them over was transparency — showing them the evidence behind each score, letting them override when they disagreed, and proving over time that the automated scores correlated with their manual assessments. That's why every signal in this prototype includes evidence quotes and reasoning, not just a number."

---

### TOPIC 7: COST & BUSINESS THINKING

**Q22: "Walk me through the cost per evaluation math."**
*Likely from: Gabe, Farshad*

> "Each conversation gets three LLM calls — resolution, sentiment, and communication. Compliance is hybrid so it has one LLM call for the adjustment. Efficiency is pure heuristic, so zero cost.
>
> With Sonnet, each call costs roughly half a cent depending on conversation length — the input is the transcript plus the rubric prompt, the output is a structured JSON with scores and reasoning. So about 1.5 cents per fully-scored conversation.
>
> Multiply that out: at a thousand conversations a day, full LLM coverage is about $15 a day. With the tiered approach — heuristic on everything, LLM on about 15 percent — it's more like $3 a day.
>
> At 100K conversations, which is the upper end for a big contact center, full coverage would be $1,500 a day. Tiered brings it to about $200. That's the kind of math that matters when you're selling to Fortune 500 customers who are doing a million conversations a month.
>
> Compare that to the cost of manual QA — a QA analyst reviewing conversations full-time might cost $60K to $80K a year and covers maybe 20 to 30 conversations a day. The automated system covers 100 percent for a fraction of that cost."

---

**Q23: "Why not fine-tune a smaller model instead of using Sonnet? Wouldn't that be cheaper?"**
*Likely from: Gabe*

> "It could be, eventually. A fine-tuned smaller model trained on enough labeled data could match Sonnet's quality on this specific task at lower inference cost. But there are tradeoffs.
>
> Fine-tuning requires labeled training data — you need hundreds or thousands of human-scored conversations to train on. That's a significant upfront investment. And then you're maintaining a model — retraining when conversation patterns change, when the customer adds new flows, when compliance rules update.
>
> The LLM-as-judge approach with prompt engineering is more flexible. You can update the rubric in the prompt tomorrow without retraining anything. When the customer changes their compliance rules, you update the prompt. When they add a new flow, you add a few lines to the knowledge base.
>
> My take: start with the prompted LLM approach, collect the human feedback over time, and when you have enough labeled data and the patterns are stable, evaluate whether a fine-tuned model gives you meaningfully better cost-performance. Don't jump to fine-tuning before you know what you're fine-tuning for."

---

### TOPIC 8: HARDER / CURVEBALL QUESTIONS

**Q24: "What's the weakest part of what you built? What would you redo?"**
*Likely from: anyone*

> "A couple things. The scoring rubrics in the prompts could be more rigorous. Right now they're based on my judgment of what good quality looks like — but every customer has different standards. An airline's compliance bar is different from a retailer's. In production, you'd co-develop the rubrics with the customer's QA team so the scoring reflects their actual standards, not mine.
>
> Second, I don't have a way to measure whether the scores are actionable — meaning, does a QA Manager who uses this tool actually coach better? The ultimate test isn't whether the scores are accurate, it's whether they lead to better outcomes. You'd need to track coaching effectiveness over time — do agents improve on the signals they were coached on?
>
> And third, the temporal features are synthetic. The timestamps are generated, not real. In production, the temporal analysis would be based on actual conversation timestamps and you'd see real patterns. The patterns I generated are plausible but they're not evidence."

---

**Q25: "If a customer says 'I don't trust AI scoring — my QA team should be the source of truth,' how do you respond?"**
*Likely from: Nimrod, Farshad*

> "They're right — and that's actually how the system should work. The QA team is the source of truth. The AI scoring is there to extend their reach, not replace their judgment.
>
> Think of it this way: the QA team manually reviews maybe 3 percent of conversations. The other 97 percent, nobody looks at. The AI scoring covers that 97 percent and surfaces the ones that are most likely to have issues. The QA team still reviews conversations, still makes the final call, and still does the coaching. They just spend less time finding problems and more time fixing them.
>
> And the feedback loop makes this concrete. When the QA Manager disagrees with an AI score, that correction feeds back into calibration. Over time, the AI scoring aligns more closely with the QA team's standards. The QA team isn't being replaced — they're training the system.
>
> At Mudflap, this was exactly the conversation we had with our customer success team. They didn't trust the automated quality scores at first. What changed their mind was seeing that the automated scores caught issues they would have caught — plus the ones they missed because they only reviewed 3 percent. Once they saw it as a coverage tool instead of a replacement tool, the resistance went away."

---

**Q26: "How do you think about quality measurement differently for AI agents versus human agents?"**
*Likely from: Farshad, Nimrod*

> "The signals are mostly the same, but the failure modes are different. A human agent might have a bad day and be short with a customer — that's a communication quality issue. An AI agent doesn't have bad days, but it can hallucinate or confidently give wrong information — that's an accuracy issue that's harder to catch.
>
> For AI agents, I'd add an 'accuracy' signal — did the agent state facts that are actually true? That's less important for human agents because they have training and institutional knowledge. AI agents can sound confident while being completely wrong, and that's the danger Nimrod wrote about with containment rate. The call looks successful on paper, but the agent gave bad information.
>
> The other big difference is consistency. Human agents vary a lot — that's why you have QA in the first place. AI agents are more consistent, but when they fail, they fail systematically. Every customer with the same issue gets the same wrong answer. So for AI agents, you're less worried about individual conversation quality and more worried about pattern detection — is there a systematic failure happening across a class of conversations."

---

**Q27: "You're a PM who codes. How do you think about the boundary between what you prototype and what engineering builds?"**
*Likely from: Farshad, Brian*

> "I prototype to learn, not to ship. The value of a PM who can build isn't that you deliver production code — it's that you make better product decisions because you've hit the real constraints.
>
> Building this case study, for example, I learned things I wouldn't have learned from a spec. Like the fact that a single LLM call per signal is way more practical than per-turn scoring — I only understood the cost and latency implications by actually running it. Or that the compliance signal needs a hybrid approach — I tried pure heuristic first, and it missed too many edge cases. Then I tried pure LLM, and it was too expensive and too slow for 100 percent coverage. The hybrid emerged from building, not from planning.
>
> But the prototype is explicitly not production code. There's no auth, no multi-tenancy, no real database, no CI/CD. In a production environment, I'd hand the architecture and the tradeoffs document to engineering and collaborate on what the production version looks like. The prototype is the conversation starter, not the final product."

---

### RAPID-FIRE REFERENCE (if questions come up you haven't rehearsed)

| Topic | Key Point |
|-------|-----------|
| **Why ABCD dataset** | It's ASAPP's own research dataset — shows I did my homework |
| **Why 200 LLM-scored** | Enough for statistical coverage across 10 flows × 30 subflows |
| **Hard block threshold** | Resolution < 0.50 OR Compliance < 0.50 — these are non-negotiable quality gates |
| **Signal weights** | Resolution 0.30, Compliance 0.25, Efficiency 0.15, Sentiment 0.15, Communication 0.15 |
| **Why weighted composite** | Not all signals are equal — failing resolution matters more than slightly low empathy |
| **Pre-computed scores** | 200 fully scored, 8K+ heuristic-scored, all precomputed so the demo is fast |
| **Streamlit choice** | Fastest path to a working dashboard for a prototype — wouldn't use it in production |
| **What I'd use in production** | React frontend, proper database (Postgres), message queue for async scoring |
| **ASAPP's CoachingAI** | Moves QA from 80% evaluating → 80% coaching. My tool automates the evaluation part |
| **Key Insights TL;DR** | Designed so the QA Manager can decide "do I need to dig deeper?" in 5 seconds |
| **Master-detail layout** | Borrowed from email clients — familiar UX, zero learning curve |
| **Why no agent-level view** | Dataset lacks agent IDs; talked about it, didn't build it — that's the right call for a prototype |
| **Why no auth** | Scope guardrail — this is a prototype, not a product. But acknowledged it in tradeoffs |

---

## MINDSET REMINDERS

1. **They're all asking the same meta-question**: "Does this person think like someone who ships production AI to enterprise customers, or like someone who built a cool demo?" Your strongest signal is the Talk About, Don't Build strategy.

2. **Lead with the user, not the tech**: When anyone asks about a feature, start with why the QA Manager needs it. Then explain how you built it. Connor and Nimrod especially will notice this.

3. **Own what you didn't build**: The confidence to say "I chose not to build that because..." is more impressive than building everything poorly. Farshad will recognize this as production maturity.

4. **Bring Mudflap naturally**: Don't force it. When a question touches on voice AI, eval frameworks, or production learnings, let the Mudflap experience come in as proof that you've done this before. The stories should feel like "oh, this reminds me of something I dealt with" — not a rehearsed pitch.

5. **Farshad is the decision-maker**: He's watching how the other four react to you. Build rapport with the whole panel, but know that he's the one deciding.

6. **Cost always matters**: ASAPP sells to Fortune 500 on cost-efficient AI. Every architectural decision should have a cost consciousness behind it. If you can mention cost savings unprompted, do it.

7. **It's a conversation, not a defense**: They're evaluating whether they want to work with you. Ask them questions back — "How does ASAPP think about this today?" or "Is that similar to how the Supervisor Suite handles it?" shows curiosity and collaborative instinct.
