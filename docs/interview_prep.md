# Interview Prep — Case Study Presentation

**Format**: 10 min intro + 10 min demo + 30 min discussion
**Panel**: Farshad (hiring mgr), Connor (design), Nimrod (product), Brian (eng), Gabe (ML eng)

---

## PART 0: WHO YOU ARE (10 minutes)

### Structure

This is the "tell us about yourself" segment. The panel knows your resume — don't recite it. Instead, tell the **scaling story** (Farshad's #1 interest), connect to **ASAPP's world**, and hit the four criteria Surai flagged: communication skills, voice experience, B2B enterprise, technical background.

**Key insight from hiring manager interview**: Farshad redirected you twice from the prototype story to "how did you scale." Lead with scaling. He also pushed for concrete specifics on security and challenged your concurrency math. Be more technical this time.

### Opening (1 min)

> "Thanks everyone for having me. I'm Minji — my background sits at the intersection of technical product management and voice AI, most recently at Mudflap where I took our voice AI product from a prototype I built personally to a production system running 500-plus calls a day across four use cases."

**Why lead with the number**: It signals 1-to-N, not just 0-to-1. Farshad wants to know you can scale, not just prototype.

---

### The Scaling Story (4 min)

> "A quick walk through how that unfolded, because the scaling decisions are what I think are most relevant to this role.
>
> We started with a problem: high-intent customers who applied for our product but never activated. Our sales team didn't have the bandwidth to follow up. So I prototyped a voice AI agent — outbound calls to these dormant leads — using Vapi for orchestration, Cartesia for TTS, Deepgram Flux for STT, and GPT-4o Mini for reasoning. I chose that model specifically for latency — sub-1,200 milliseconds end-to-end, because our data showed that anything over 1.5 seconds triggered hang-ups.
>
> The prototype was rough. 60 percent hang-up rate on the first iteration. I worked through that systematically — personalized greetings by injecting CRM context so the bot said 'Hi Sarah' instead of a generic hello, agent-talks-first timing to hook the customer before they could decide it was spam, and keyword boosting in Deepgram to handle our users' accents in noisy environments. That brought hang-ups down to 10 percent.
>
> Once we proved 18 percent conversion on connected calls, I went to our CEO and got real resources — engineering headcount, a sales ops partner, and an enterprise vendor contract. That's where the scaling decisions started.
>
> On the vendor side, I evaluated Cartesia versus ElevenLabs for TTS. ElevenLabs had higher voice quality but sounded too polished for our customer base — truck drivers perceived it as robotic. Cartesia's voices had more natural imperfections that resonated better. For eval tooling, I specifically chose Future AGI over Braintrust and Langfuse because they could evaluate audio natively — not just transcribed text — which meant we could catch prosody and dead air issues that text-based evals completely missed.
>
> On the technical side, I built a four-stage deployment pipeline — test, staging with bot-to-bot simulation across 50 scenarios, pre-production, and production — with quality gates at each stage. If our golden set of annotated transcripts showed score regression beyond 5 points, the deployment stopped. That was non-negotiable.
>
> On the data and security side, I negotiated PII handling terms in the enterprise contract — specifically, a right-to-delete clause for call recordings and a commitment from the vendor not to train on our customer data. Beyond the contract, we implemented PII redaction in the transcript pipeline before anything hit our eval tools, so sensitive information like account numbers never left our boundary.
>
> We scaled from one use case at 200 calls per day to four use cases at 500-plus — outbound reactivation, inbound routing, appointment scheduling, and application status checks. The inbound system used Twilio for telephony and tool-called into our HubSpot CRM for real-time context."

**Why this version is better than the Farshad interview**: It leads with scaling, gives concrete vendor evaluation specifics (he wanted that), gives a real security answer (PII redaction, not just contractual), and naturally hits voice depth without being asked.

---

### Why ASAPP (2 min)

> "That experience is what drew me to ASAPP. At Mudflap, voice AI was one product within a larger platform. At ASAPP, voice is the core — you have a dedicated voice engineering team, a research team with its own C-level working on speech-to-speech models, your own streaming cascade architecture, and enterprise customers operating at a scale that's orders of magnitude beyond what I built.
>
> The scope of this role is also what excites me. It's not just voice in isolation — it's voice plus the adjacent agentic ecosystem. Telephony integrations with CCaaS platforms like Amazon Connect and Genesys, payments over voice, SIP connectivity, IVR routing. These are exactly the kinds of integration problems I ran into at Mudflap at a smaller scale — we had Twilio for telephony and HubSpot for CRM, but at ASAPP you're dealing with Fortune 500 contact centers where those integrations are the product.
>
> And the way product works here — hands-on, prototyping, influence-based rather than top-down authority — that's exactly how I operate. The case study I'm about to show you is a working prototype I built end to end, not a spec."

**Why this matters**: It references specific things Farshad told you — S2S research, streaming cascade, adjacent ecosystem, CCaaS integrations, "PMs build" culture. Shows you listened and did your homework.

---

### Transition to Demo (30 sec)

> "So with that context, let me show you what I built for the case study — a Conversation Quality Reviewer. I'll walk through the prototype, then the decisions behind it, and then I'd love to dig into the discussion."

---

## PART 1: PROTOTYPE WALKTHROUGH (10 minutes)

### Opening (1 min)

> "Farshad, you mentioned that PMs here build. So I built this.
>
> This is a Conversation Quality Reviewer — it ingests batch transcripts, computes five quality signals per conversation, and surfaces the results through a FastAPI API and this Streamlit dashboard. It's essentially a mini version of what CoachingAI does — automate quality evaluation for 100 percent of interactions so the QA Manager spends her time coaching, not reviewing. The signal framework maps to CoachingAI's pillars: compliance maps to Automatic Compliance, resolution and communication map to Topic Mastery. And the Review Queue is similar in spirit to what Nimrod's team built with Conversation Explorer — transcripts plus reasoning plus a quality tab for flagged interactions.
>
> The lens I used to build everything: I defined the primary user as a QA Manager at an airline contact center — someone like a JetBlue QA lead who manually samples maybe 1 to 5 percent of conversations. The rest is a blind spot. Every feature had to answer one question: what does the QA Manager do with this information? If I couldn't answer that, I talked about it in the tradeoffs note instead of building it."

**Why this opening works**: It directly references Farshad's words (rapport), connects to CoachingAI (shows ASAPP knowledge), signals persona-driven thinking (for Connor), outcome orientation (for Nimrod), and the "talk about, don't build" discipline (for Farshad). All in 45 seconds.

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

> "Below the table, there's a horizontal bar chart showing average scores across the five signals — Resolution, Compliance, Efficiency, Sentiment, and Communication. If I use Nimrod's framework from his 'Beyond Containment' blog, these map to Goal Completion, Accuracy and Guardrails, task efficiency, Customer Friction, and Conversation Fluency.
>
> There's also a Quality Trend line chart showing daily average quality over time — so the QA Manager can see if quality is improving or degrading — and a Failure Pattern Map plotting Resolution against Compliance with quadrant shading. Each quadrant tells the QA Manager what to do: policy gap means retrain on process, resolution gap means fix the tools or knowledge base, both failing means escalate. I'll be honest — the failure pattern map is more useful for weekly reviews than daily triage. If I had another week, I'd move it to a secondary analytics view and keep the main page focused on the table, KPIs, and trend line."

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

### Stop 5: Architecture, Scale & What I Chose Not to Build (2 min)

> "Under the hood, the architecture is straightforward. Conversations come in, go through an ingest layer, hit a scoring engine that runs five signal computers, and the results are served through a FastAPI API. The dashboard is just one consumer of that API — a customer could build their own integration, pipe scores into their existing tools, whatever works for them.
>
> One design choice I want to highlight: I use three LLM calls per conversation, not ninety. Instead of scoring each turn individually, each signal gets a single call with the full conversation context. That's a deliberate cost decision — at scale, the difference between 3 and 90 API calls per conversation is the difference between viable and not viable.
>
> And I tier the scoring: heuristics run on every conversation for free — turn count, action sequence matching. LLM scoring only runs on flagged conversations plus a random sample. At 100K conversations a day, that's about $200 a day instead of $1,500. That mirrors how ASAPP's cascade architecture already works — cheap models filter, expensive models refine. And it fits into the CXP flywheel Farshad wrote about — quality scoring is the measurement layer that feeds the Optimization and Insights agents.
>
> Now let me call out what I deliberately chose NOT to build. No human feedback loop — because calibration requires labeled data from real QA teams, not synthetic examples. No agent-level aggregation — because the ABCD dataset doesn't have agent IDs, and building it without real data would be dishonest. No real-time scoring — because this is a batch QA review tool; the QA Manager reviews after the fact. ASAPP's streaming cascade handles real-time, and this would complement it as the post-call analysis layer. No voice or audio features — because this is text-only, but the signal framework is designed so you can swap text-based signal computers for audio-based ones when the input changes.
>
> I'd rather talk about these decisions than build half-baked versions — because knowing what not to build is as much a product decision as knowing what to build."

**Decision to highlight if asked**: "The API is the real product. The dashboard is a view. That matters because enterprise customers — especially airlines and telecoms — have their own dashboards, their own BI tools. If the quality reviewer is locked behind one UI, it's not useful. The API-first design means it fits wherever the customer already works."

---

### Closing the Demo (30 sec)

> "That's the prototype and the decisions behind it. I'd love to dig into any of this — the signals, the architecture, what changes for voice, what I'm unsure about, or how this would fit into ASAPP's platform."

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
> I actually found strong validation for these choices after reading Nimrod's blog post on moving beyond containment. He proposes a holistic scoring model — Goal Completion, Accuracy and Guardrails, Deep Observability, Conversation Fluency, Customer Friction. My Resolution maps to Goal Completion, Compliance to Accuracy and Guardrails, Communication to Conversation Fluency, Sentiment to Customer Friction. It was encouraging to see the alignment.
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

> "The API is the integration surface. The dashboard is just one consumer — it hits the same endpoints any other system would. A customer could pipe quality scores into their existing BI tool, their workforce management system, or ASAPP's own Interaction Intelligence layer.
>
> The API contract is clean — you send conversation IDs, you get back structured scores with evidence and reasoning. In ASAPP's world, this sits within the CXP flywheel that Farshad wrote about. Conversations come in through telephony, flow through the streaming cascade during the call, and after the call ends, the quality reviewer picks up the transcript asynchronously. Scores feed back into the Optimization Agent for continuous improvement and into the Insights Agent for pattern detection. The Supervisor Suite — Nimrod's domain — consumes those scores through Conversation Explorer for the supervisor's review workflow.
>
> In ASAPP's integrations ecosystem, the quality scorer becomes an MCP server that any agent or tool can invoke. The Developer Agent could use it as a test harness when building new workflows. The Simulation Agent could use it to validate quality before deployment.
>
> One thing I was intentional about: the quality reviewer doesn't own the conversation data. It reads transcripts and writes scores. It doesn't need to know about the telephony stack, the ASR pipeline, or the agent routing. That separation means it plugs into the platform without disrupting anything."

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

> "Honestly, I'd remove more than I'd add. The Failure Pattern Map — the resolution-vs-compliance scatter — is useful for quarterly pattern analysis but the QA Manager doesn't need it at 7:30 AM. I'd move it to a secondary analytics view.
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

### TOPIC 4B: VOICE & SPEECH-TO-SPEECH

**Q28: "Tell me about speech-to-speech models and how they relate to what ASAPP is building."**
*Likely from: Brian, Farshad, Gabe*

> "Today, voice AI runs on a cascade — audio comes in, ASR converts it to text, the LLM reasons over the text, TTS converts the response back to audio. Three separate models chained together. That's what ASAPP runs in production right now with AutoTranscribe plus their GenerativeAgent.
>
> The cascade works, but it has tradeoffs. Each stage adds latency — you're looking at 1 to 3 seconds end-to-end. And you lose information at the ASR step. Tone, hesitation, emphasis — all the paralinguistic signals that tell you how someone feels, not just what they said. A customer can say 'that's fine' in a way that clearly means it's not fine, and the text transcript loses that entirely.
>
> Speech-to-speech models collapse that cascade into a single model that takes audio in and produces audio out directly. No intermediate text. That means sub-400ms latency — which is within the natural human response window — and you preserve all the acoustic information.
>
> ASAPP is actively working on this. Their DiscreteSLU paper at Interspeech 2024 shows they're integrating speech directly into LLMs using discrete speech units — that's a stepping stone toward full S2S. And their 'Architecture of Trust' blog explicitly says they're building native S2S to collapse the cascade into 'a single, unified neural loop.'
>
> The reason the cascade still dominates in production is practical. Tool use, function calling, compliance guardrails — all of that is solved in the text layer. S2S embeds reasoning in trained weights, so upgrading the model means expensive end-to-end retraining. For enterprise customers handling millions of calls with regulatory requirements, debuggability matters.
>
> The PM question — which is what this role would own — is when and how to transition. It's not a flip-the-switch moment. You'd run them in parallel, validate S2S quality against the cascade, and migrate use cases incrementally. The job listing actually calls this out — it says the voice PM owns 'the underlying model bets.'"

**If they ask "How does S2S affect quality scoring?"**

> "It's actually a big opportunity for what I built. Right now, the quality scorer works on text transcripts — which means ASR errors propagate into the scores. If the transcript says the agent said something they didn't actually say, the compliance and resolution scores can be wrong.
>
> With S2S, you could score directly from audio. The signal framework stays the same — you're still measuring resolution, compliance, efficiency, sentiment, communication. But the inputs change. Sentiment gets way richer — you're reading tone, not just words. Efficiency shifts from turn count to handle time, dead air, and hold time. Communication picks up filler words, speech rate, interruptions.
>
> And you eliminate the transcription error layer entirely. That's a meaningful accuracy improvement for quality scoring."

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
> First, the human feedback loop — or what ASAPP calls the HILA philosophy applied to quality evaluation. That disabled 'Add Feedback' button isn't decoration — it's the anchor for the most important feature the product needs. When the QA Manager disagrees with a score, she should be able to correct it, the same way a HILA supervisor provides targeted guidance that the AI learns from. Those corrections become calibration data. Over time, you measure LLM-vs-human agreement and tune the rubrics. Without that loop, the system doesn't improve — and that feedback loop is what makes the CXP flywheel actually spin.
>
> Second, agent-level aggregation. Right now this is conversation-level — you see individual conversations. But the QA Manager coaches agents, not conversations. She needs to see: 'Agent Sarah averages 0.82 overall but 0.55 on compliance in refund calls.' That's a specific, actionable coaching target. This is what CoachingAI already does with its three pillars — Automatic Compliance, Topic Mastery, Tool Mastery — but aggregated to the agent level. The dataset I used didn't have agent IDs, so I couldn't build this, but the data model supports it.
>
> Third, regression detection. When you push a new prompt, change a model, or update a compliance rubric, scores shift. You need to know whether they shifted intentionally or broke something. That maps to the Simulation Agent's role in the CXP lifecycle — validate before you ship, and monitor after you ship.
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

> "They're right — and that's actually how the system should work. The QA team is the source of truth. The AI scoring extends their reach, not replaces their judgment. This is exactly the HILA philosophy ASAPP already uses — the human isn't a fallback, they're an embedded collaborator who makes the AI better.
>
> Think of it this way: the QA team manually reviews maybe 3 percent of conversations. The other 97 percent, nobody looks at. The AI scoring covers 100 percent of interactions and surfaces the ones that need attention. The QA team still reviews conversations, still makes the final call, and still does the coaching. They just spend less time finding problems and more time fixing them. That's the CoachingAI promise — move from 80 percent evaluating to 80 percent coaching.
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

### TOPIC 9: WALK THROUGH YOUR DECISIONS — BUILT, NOT BUILT, AND WHY

*This directly addresses the case study prompt: "Walk through your decisions. What you built, what you chose not to build, and why."*

**Q29: "Walk me through your major decisions. What did you build, what did you skip, and why?"**
*Likely from: Farshad, anyone*

> "Let me walk through the decision tree.
>
> I started with the user. I defined a QA Manager at an airline contact center as my primary persona — someone who reviews conversations daily, identifies coaching targets, and escalates systemic issues. That persona filtered everything. If a feature didn't answer 'what does the QA Manager do with this?' — I didn't build it.
>
> For signals, I chose five — resolution, efficiency, compliance, sentiment, and communication — because they map to the five questions contact center leaders actually ask: did we solve it, how much did it cost, did we follow the rules, is the customer happy, and is the agent coachable. I rejected agent knowledge accuracy because it overlaps with compliance, transfer rate because it's not in the ABCD data, and first-contact resolution because you can't determine it from a single transcript without session linking.
>
> For the scoring approach, I went hybrid. Efficiency is pure heuristic — turn count and action sequences are structural, a language model adds zero value over counting. Compliance is hybrid — the heuristic catches 80 percent of violations through action-sequence matching against the ABCD knowledge base, and the LLM handles justified deviations. The other three are LLM-based because semantic judgment is required. I deliberately chose Sonnet over Opus — structured scoring tasks don't need Opus-level reasoning, and at 5x the cost, defaulting to the most expensive model would contradict how ASAPP thinks about cost-efficient AI.
>
> For the dashboard, I built two views: Quality Summary for 'how are we doing' and Review Queue for 'which calls need attention.' I started with three views but the third — a standalone conversation detail — duplicated what the Review Queue already showed inline. So I cut it. That kind of subtraction is a product decision too.
>
> What I explicitly chose NOT to build: human feedback loops, because calibration requires labeled data from real QA teams. Agent-level aggregation, because the ABCD dataset lacks agent IDs and building it on fake data would be dishonest. Real-time scoring, because this is a batch QA review tool — ASAPP's streaming cascade handles real-time. Authentication and multi-tenancy, because they're infrastructure decisions, not product decisions, and spending 8 hours on auth would have been 8 hours not spent on the scoring framework.
>
> Each of those is documented in my decisions log with the rationale. I'd rather talk about these decisions credibly than build half-baked versions."

---

**Q30: "You said you chose Sonnet over Opus. Walk me through that decision more concretely."**
*Likely from: Gabe, Farshad*

> "Three factors. First, task fit — these are structured evaluation tasks: read a transcript, evaluate against criteria, return JSON. Sonnet handles that reliably. I'm not asking for creative reasoning or complex multi-step chains. Second, cost — Sonnet is about 1.5 cents per conversation for three LLM calls. Opus would be about 7.5 cents. At 10K conversations a day, that's $150 versus $750. Tiered with heuristic pre-filtering, Sonnet comes to about $25 a day. Third, and this is the one I care about most — ASAPP builds cost-efficient AI for Fortune 500 contact centers. Walking into this interview having defaulted to the most expensive model for everything would signal the opposite of how you think about AI at scale. I used Haiku as a screening option and Opus as a calibration tiebreaker — Sonnet is the production workhorse."

---

### TOPIC 10: WHAT I'D CHANGE, MEASURE, AND WHAT I'M UNSURE ABOUT

*This directly addresses the case study prompt: "Talk tradeoffs. What you'd change for production, what you'd measure, what you're unsure about."*

**Q31: "What would you change for production?"**
*Likely from: Farshad, Brian*

> "Five things, in priority order.
>
> First, tiered scoring pipeline. The prototype runs full LLM scoring on every conversation. At 100K per day that's $1,500. Production needs tiers — heuristics on everything, LLM on flagged plus a random sample. That's the same cascade philosophy ASAPP uses — cheap models filter, expensive models refine.
>
> Second, anchored rubrics. Right now my LLM signals define scoring dimensions but not calibrated score levels. In production, each score level gets 2 to 3 annotated example conversations from the customer's QA team, embedded as few-shot examples. That turns the LLM judge from directional to grounded.
>
> Third, persistent storage and async processing. Replace JSON file storage with Postgres, score conversations through a job queue, not synchronously per request.
>
> Fourth, agent-level aggregation. That's what transforms this from a conversation review tool into a coaching product — 'Agent Smith resolves 90 percent of cases but empathy is at 0.35, here are three example conversations.'
>
> Fifth, voice and audio signals. Text is where I started because the dataset is text. But for ASAPP's voice product, sentiment gets prosody analysis, efficiency shifts to handle time and dead air, communication picks up filler words and speech rate. The signal framework stays the same — you swap the signal computers."

---

**Q32: "What would you measure to know this is working?"**
*Likely from: Gabe, Farshad*

> "Five things.
>
> LLM-versus-human agreement — have three QA analysts score 200 conversations, measure Cohen's kappa per signal, target above 0.7. Where the LLM disagrees with consensus, tune the rubric. Where humans disagree with each other, tighten the signal definition.
>
> Score-CSAT correlation — if conversations scored as high quality consistently get low CSAT, the scoring framework is measuring the wrong thing. That's the external validation layer.
>
> Drift monitoring — run the golden set monthly and alert on distribution shifts. When Anthropic updates the model, scores can shift without you changing anything. You need to catch that.
>
> Operational metrics — latency per conversation, API error rate, cost per scored conversation. These are the health check on the pipeline itself.
>
> And the one that matters most and is hardest to measure: coaching effectiveness. Do agents who get coached based on these scores actually improve on those signals over time? If the scores are accurate but they don't lead to better outcomes, the product isn't working."

---

**Q33: "What are you unsure about? What keeps you up at night with this approach?"**
*Likely from: anyone — this is a maturity test*

> "Three things I'm genuinely unsure about.
>
> First, whether a composite quality score is even the right abstraction. I use it as a sorting heuristic for the queue, but collapsing five different dimensions into one number feels like it loses more than it gains. A conversation with 0.95 resolution and 0.30 compliance is very different from one with 0.60 across the board, but they might get the same composite score. I'm not sure a weighted average is the right aggregation — maybe it should be 'worst signal wins' for queue prioritization, or maybe the composite should be replaced entirely by a priority tier that's driven by the hard-block logic. I built it because QA managers expect a single number, but I'm not convinced it's the right design.
>
> Second, whether LLM-as-judge is stable enough for production quality scoring. Run-to-run variance is small — maybe plus or minus 0.03 — but model updates from Anthropic could shift scores across the board. That's manageable with golden sets, but it means you're maintaining an eval pipeline for your eval pipeline, which is a real operational cost. I'm not sure the maintenance burden scales gracefully to dozens of enterprise customers with different rubrics.
>
> Third, whether per-conversation scoring is even the right unit of analysis for the QA Manager's workflow. She coaches agents, not conversations. Without agent IDs, this tool tells her 'here are bad conversations' but not 'here's who needs coaching.' That agent-level aggregation is what transforms this from a search tool into a coaching product, and I'm unsure how much value the conversation-level view provides on its own without it."

**Why this answer is strong**: It shows genuine uncertainty, not false humility. Each doubt is specific, reasoned, and reveals a deeper understanding of the problem. Farshad will respect this more than "I'd just add more features."

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
| **ASAPP's CoachingAI** | Moves QA from 80% evaluating → 80% coaching. Three pillars: Automatic Compliance, Topic Mastery, Tool Mastery |
| **Nimrod's framework** | "Beyond Containment" blog: Goal Completion, Accuracy & Guardrails, Observability, Fluency, Friction |
| **Farshad's framework** | "Architecture of Trust" blog: technical resilience, functional trust, task efficiency |
| **Devidas's framework** | Empirical (FCR, error rate, latency, learning velocity) + Experiential (CSAT, sentiment drift, trust signals) |
| **CXP flywheel** | Discovery → Developer → Simulation → Optimization → Insights. Quality reviewer is the measurement layer |
| **Conversation Explorer** | ASAPP's existing tool: transcripts + AI reasoning + quality tab. My Review Queue is similar in spirit |
| **HILA** | Human-in-the-Loop Agent: embedded collaboration, not escalation. QA feedback loop follows same philosophy |
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
