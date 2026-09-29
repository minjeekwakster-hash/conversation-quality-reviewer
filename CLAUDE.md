# Conversation Quality Reviewer — Project Context

## What We're Building
A prototype Conversation Quality Reviewer for ASAPP's case study interview. It ingests batch conversation transcripts (ABCD v1.1 dataset), computes 5 quality signals per conversation (Resolution, Efficiency, Compliance, Sentiment, Communication), and exposes results via a FastAPI API and Streamlit dashboard. The goal is to demonstrate product judgment, technical depth, and production thinking to a panel of Engineering, Research, Design, and Customer Engineering evaluators.

## ASAPP Company Context
ASAPP builds enterprise AI for contact centers. Customers are Fortune 500 companies — airlines (JetBlue, American Airlines), telecoms (4 of top 10), banks, and insurance. They care about **cost-efficient AI at scale**, not the most expensive model. Their CoachingAI product automates QA for 100% of interactions, moving QA managers from 80% evaluating to 80% coaching. ASAPP has an in-house research team (with own C-level) working on speech-to-speech models, a dedicated voice engineering team, and their own streaming cascade platform.

## Primary Persona: QA Manager at JetBlue
The dashboard's primary user is a **QA Manager** at an airline contact center — not a Head of CS, not a data analyst. This person:
- Reviews conversation quality daily, identifies coaching targets, and escalates systemic issues
- Currently drowns in manual review (sampling only 1-5% of calls), needs 100% visibility
- Makes decisions about: who to coach, what to retrain, which processes to change, what to escalate
- See `docs/persona.md` for full persona research

## Design Principles
- **Every feature must answer**: "What does the QA Manager do with this information?"
- Features that can't answer that question should be **talked about, not built**
- Prioritize **actionability** over comprehensiveness
- Use plain language and familiar patterns (email/ticketing UX, not data science UX)

## Scope Guardrails

### Don't Build
- Real-time/streaming scoring (this is batch review)
- User authentication or multi-tenancy
- Agent-level aggregation (ABCD dataset lacks agent IDs)
- Audio/voice features (text-only prototype)
- Custom signal configuration UI
- Persistent database (JSON file storage is fine for prototype)

### Do Talk About (in presentation)
- Human feedback / coach's notes and how it calibrates the LLM judge
- Calibration loop (LLM judge vs. human agreement, Cohen's kappa)
- Grounded rubrics and eval criteria documentation
- Regression detection (score drift over time)
- Agent-level aggregation and coaching workflows

## Key Files
- `docs/decisions.md` — Decision log with rationale for every design choice
- `docs/persona.md` — QA Manager persona research
- `tradeoffs.md` — One-page tradeoffs note (case study deliverable)
- `dashboard/app.py` — Streamlit dashboard (2 views: Quality Summary, Review Queue)
- `src/` — Backend: models, signals, scoring engine, ingest
- `scripts/seed_data.py` — Pre-compute scores for demo
