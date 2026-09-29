"""FastAPI endpoints for the Conversation Quality Reviewer."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from pydantic import BaseModel

from .engine import ScoringEngine
from .ingest import (
    DATA_DIR,
    load_dataset,
    load_kb,
    load_precomputed,
    load_sample,
    stratified_sample,
)
from .models import BatchResult, BatchSummary, ConversationResult
from .signals.efficiency import EfficiencySignal

load_dotenv()

app = FastAPI(
    title="Conversation Quality Reviewer",
    description="Batch quality scoring for customer service conversations using the ABCD dataset.",
    version="1.0.0",
)

# --- Global state ---
_engine: Optional[ScoringEngine] = None
_conversations: dict[int, object] = {}  # convo_id -> Conversation
_batches: dict[str, BatchResult] = {}
_precomputed: dict[int, ConversationResult] = {}


def _get_engine() -> ScoringEngine:
    global _engine
    if _engine is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        client = anthropic.AsyncAnthropic(api_key=api_key) if api_key else None
        try:
            kb = load_kb()
        except FileNotFoundError:
            kb = {}
        _engine = ScoringEngine(
            anthropic_client=client,
            kb=kb,
            llm_enabled=client is not None,
        )
    return _engine


def _load_conversations():
    """Load conversations and precomputed scores at startup."""
    global _conversations, _precomputed

    # Try loading dataset
    try:
        convos = load_dataset("train")
    except FileNotFoundError:
        try:
            convos = load_sample()
        except FileNotFoundError:
            convos = []

    _conversations = {c.convo_id: c for c in convos}

    # Load precomputed scores
    precomputed_raw = load_precomputed()
    for raw in precomputed_raw:
        try:
            result = ConversationResult(**raw)
            _precomputed[result.convo_id] = result
        except Exception:
            continue


# --- Request/Response Models ---

class AnalyzeRequest(BaseModel):
    convo_ids: Optional[list[int]] = None  # Specific IDs, or None for sample
    sample_size: int = 10
    use_llm: bool = True


class AnalyzeResponse(BaseModel):
    batch_id: str
    total: int
    status: str


# --- Startup ---

@app.on_event("startup")
async def startup():
    _load_conversations()


# --- Endpoints ---

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "conversations_loaded": len(_conversations),
        "precomputed_scores": len(_precomputed),
        "llm_available": os.getenv("ANTHROPIC_API_KEY") is not None,
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Submit a batch of conversations for scoring. Runs in background."""
    engine = _get_engine()
    batch_id = str(uuid.uuid4())[:8]

    if request.convo_ids:
        convos = [
            _conversations[cid]
            for cid in request.convo_ids
            if cid in _conversations
        ]
        if not convos:
            raise HTTPException(404, "None of the specified convo_ids were found.")
    else:
        all_convos = list(_conversations.values())
        convos = all_convos[: request.sample_size]

    batch = BatchResult(batch_id=batch_id, total=len(convos), status="running")
    _batches[batch_id] = batch

    async def _run_batch():
        result = await engine.score_batch(convos, batch_id=batch_id)
        _batches[batch_id] = result
        # Also cache individual results
        for r in result.results:
            _precomputed[r.convo_id] = r

    background_tasks.add_task(_run_batch)

    return AnalyzeResponse(batch_id=batch_id, total=len(convos), status="running")


@app.get("/results/{batch_id}", response_model=BatchResult)
async def get_results(batch_id: str):
    """Get results for a batch (partial if still running)."""
    if batch_id not in _batches:
        raise HTTPException(404, f"Batch {batch_id} not found.")
    return _batches[batch_id]


@app.get("/conversation/{convo_id}", response_model=ConversationResult)
async def get_conversation(convo_id: int):
    """Get scores for a single conversation. Returns precomputed if available."""
    # Check precomputed first
    if convo_id in _precomputed:
        return _precomputed[convo_id]

    # Score on-demand (heuristic only if no API key)
    if convo_id not in _conversations:
        raise HTTPException(404, f"Conversation {convo_id} not found.")

    engine = _get_engine()
    result = await engine.score_conversation(_conversations[convo_id])
    _precomputed[convo_id] = result
    return result


@app.get("/conversations", response_model=list[ConversationResult])
async def list_conversations(
    flow: Optional[str] = Query(None, description="Filter by flow"),
    subflow: Optional[str] = Query(None, description="Filter by subflow"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    scored_after: Optional[datetime] = Query(None, description="Filter to conversations scored after this ISO timestamp"),
    scored_before: Optional[datetime] = Query(None, description="Filter to conversations scored before this ISO timestamp"),
    flagged_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List scored conversations with optional filters."""
    results = list(_precomputed.values())

    if flow:
        results = [r for r in results if r.flow == flow]
    if subflow:
        results = [r for r in results if r.subflow == subflow]
    if min_score is not None:
        results = [r for r in results if r.overall_score >= min_score]
    if max_score is not None:
        results = [r for r in results if r.overall_score <= max_score]
    if scored_after is not None:
        results = [r for r in results if r.scored_at and r.scored_at >= scored_after]
    if scored_before is not None:
        results = [r for r in results if r.scored_at and r.scored_at < scored_before]
    if flagged_only:
        results = [r for r in results if r.flags]

    # Sort by overall score ascending (worst first for review)
    results.sort(key=lambda r: r.overall_score)

    return results[offset : offset + limit]


@app.get("/summary", response_model=BatchSummary)
async def get_summary(flow: Optional[str] = Query(None)):
    """Aggregate metrics across all scored conversations."""
    results = list(_precomputed.values())
    if flow:
        results = [r for r in results if r.flow == flow]

    if not results:
        return BatchSummary()

    engine = _get_engine()
    mock_batch = BatchResult(
        batch_id="summary",
        total=len(results),
        completed=len(results),
        results=results,
        status="completed",
    )
    return engine.summarize(mock_batch)


@app.get("/flows")
async def list_flows():
    """List all available flows and subflows with conversation counts."""
    from collections import defaultdict

    flow_counts = defaultdict(lambda: defaultdict(int))
    for c in _conversations.values():
        flow_counts[c.scenario.flow][c.scenario.subflow] += 1

    return {
        flow: dict(subflows) for flow, subflows in sorted(flow_counts.items())
    }


@app.get("/conversation/{convo_id}/transcript")
async def get_transcript(convo_id: int):
    """Get the raw transcript for a conversation."""
    if convo_id not in _conversations:
        raise HTTPException(404, f"Conversation {convo_id} not found.")

    convo = _conversations[convo_id]
    return {
        "convo_id": convo_id,
        "flow": convo.scenario.flow,
        "subflow": convo.scenario.subflow,
        "customer_name": convo.scenario.personal.customer_name,
        "member_level": convo.scenario.personal.member_level,
        "turns": [
            {"speaker": t.speaker.value, "text": t.text}
            for t in convo.original
        ],
        "actions_taken": convo.actions_taken,
    }
