# QA Manager Persona — JetBlue Contact Center

## Who They Are
**Role**: Quality Assurance Manager at JetBlue's contact center operation
**Reports to**: Director of Customer Experience or VP of Operations
**Team**: 2-4 QA analysts who do hands-on evaluations; the QA Manager sets standards, reviews escalations, and reports up

## Day-to-Day Workflow
1. **Morning**: Check overnight quality dashboards — are any call types trending down? Any compliance incidents?
2. **Triage**: Review flagged interactions (currently 1-5% sample; goal is 100% automated coverage)
3. **Coaching prep**: Pull 3-5 examples of specific issues to use in agent coaching sessions
4. **Scorecard maintenance**: Update evaluation rubrics when policies change (fare rules, refund policies, ID verification requirements)
5. **Compliance audits**: Verify agents follow identity verification, fare disclosure, and PCI-DSS rules for payment handling
6. **Reporting**: Weekly quality summary to leadership — trends, coaching outcomes, escalations

## Core KPIs They Track
| KPI | Why It Matters |
|-----|---------------|
| **QA Score** (composite) | Overall quality health — the single number leadership asks about |
| **First Contact Resolution (FCR)** | Did we solve it without a callback? Directly tied to cost and CSAT |
| **CSAT / NPS** | Customer happiness — lagging indicator but the one execs care about |
| **Average Handle Time (AHT)** | Cost driver — but can't optimize at the expense of quality |
| **Compliance Rate** | Non-negotiable in regulated industries (airline ticket rules, PCI) |
| **Coaching Completion Rate** | Are agents actually improving after feedback? |

## Pain Points (Current State)
- **Blind spots**: Only reviews 1-5% of calls — the other 95% could have issues she never sees
- **Siloed tools**: QA scores in one tool, CSAT in another, compliance in a spreadsheet, coaching notes in email
- **Slow time-to-insight**: By the time she identifies a trend, it's been happening for weeks
- **Coaching moments expire**: The agent can't remember the specific call by the time feedback arrives days later
- **Inconsistent scoring**: Different QA analysts score differently — no calibrated rubric
- **Can't prioritize**: Without automated flagging, she reviews calls randomly or by customer complaint, missing systemic issues

## Decisions They Make
| Decision | Trigger | Action |
|----------|---------|--------|
| Who to coach | Low scores on specific signals | Pull 3-5 example calls, schedule 1:1 |
| What to retrain | Signal consistently low across a call type | Request targeted training module |
| Which process to change | High compliance failures in one flow | Escalate to ops: "The refund workflow is broken" |
| What to escalate | Systemic quality drop >5pts | Report to leadership with root cause |
| Who to recognize | Consistently above bar | Nominate for recognition, share as examples |

## What They Need From This Tool
1. **Aggregate health at a glance**: "How are we doing?" answered in 5 seconds
2. **Surface the 5-10% that need human review**: Don't make me find the problems — show me
3. **Drill down by call reason**: Quality issues are always specific to a workflow, not universal
4. **Highlight compliance risks**: In aviation, a missed identity verification is a potential security incident — it can't hide in the average
5. **Link scores to specific call moments**: "The score is 0.45 because the agent skipped step 3" — not just a number
6. **Trend over time** (future): "Is this getting better or worse since last week's training?"

## ASAPP Alignment
ASAPP's CoachingAI promises to move QA managers from **80% evaluating → 80% coaching**. Our prototype demonstrates this shift:
- Automated scoring replaces manual evaluation of every call
- Priority-sorted review queue replaces random sampling
- Issue summaries in plain language replace listening to full recordings
- The QA Manager's time shifts from "find the problem" to "fix the problem"
