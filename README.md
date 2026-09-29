# Conversation Quality Reviewer

A prototype quality scoring system for customer service conversations. Ingests batch transcripts, computes 5 quality signals (heuristic + LLM-based), and exposes results via a REST API and interactive dashboard.

Built using the [ABCD dataset](https://github.com/asappresearch/abcd) (10K human-to-human customer service dialogues).

## Quality Signals

| Signal | Type | What It Measures |
|--------|------|-----------------|
| **Resolution Effectiveness** | LLM | Did the agent resolve the customer's issue? |
| **Conversation Efficiency** | Heuristic | Turn count vs. baseline, substantive turn ratio |
| **Policy Compliance** | Hybrid | Action sequence adherence + nuanced policy application |
| **Customer Sentiment Trajectory** | LLM | Per-turn sentiment arc, frustration spikes, recovery |
| **Agent Communication Quality** | LLM | Clarity, empathy, professionalism, proactiveness |

## Quick Start

### 1. Install dependencies
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Download the ABCD dataset
```bash
python scripts/download_data.py
```

### 3. Set up your API key
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 4. Pre-compute scores for the demo
```bash
# Heuristic only (instant, no API key needed)
python scripts/seed_data.py --heuristic-only

# Full scoring with LLM (~30 min, requires API key)
python scripts/seed_data.py --sample-size 20
```

### 5. Start the API server
```bash
uvicorn src.api:app --reload --port 8000
```

### 6. Launch the dashboard
```bash
streamlit run dashboard/app.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | Submit conversations for scoring (background) |
| `GET` | `/results/{batch_id}` | Batch results (partial if running) |
| `GET` | `/conversation/{convo_id}` | Single conversation scores |
| `GET` | `/conversations` | List/filter scored conversations |
| `GET` | `/summary` | Aggregate metrics and distributions |
| `GET` | `/flows` | Available flows and subflows |
| `GET` | `/health` | System status |

## Architecture

```
                    ┌─────────────────┐
                    │   Streamlit     │
                    │   Dashboard     │
                    └────────┬────────┘
                             │ HTTP
                    ┌────────▼────────┐
                    │   FastAPI       │
                    │   REST API      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Scoring Engine │
                    │  (orchestrator) │
                    └────────┬────────┘
            ┌────────┬───────┼───────┬────────┐
            ▼        ▼       ▼       ▼        ▼
        Resolution Efficiency Compliance Sentiment Communication
         (LLM)   (heuristic) (hybrid)    (LLM)      (LLM)
```

## Project Structure

```
├── src/
│   ├── models.py          # Pydantic data models
│   ├── ingest.py          # Dataset loading & parsing
│   ├── engine.py          # Signal orchestrator
│   ├── api.py             # FastAPI endpoints
│   └── signals/
│       ├── base.py        # Abstract signal interface
│       ├── efficiency.py  # Heuristic signal
│       ├── resolution.py  # LLM signal
│       ├── compliance.py  # Hybrid signal
│       ├── sentiment.py   # LLM signal
│       └── communication.py # LLM signal
├── dashboard/
│   └── app.py             # Streamlit dashboard (3 views)
├── scripts/
│   ├── download_data.py   # Download ABCD dataset
│   └── seed_data.py       # Pre-compute demo scores
├── docs/
│   └── decisions.md       # Design decision log
└── tradeoffs.md           # One-page tradeoffs note
```
