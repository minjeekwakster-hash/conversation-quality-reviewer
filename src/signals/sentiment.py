"""Customer Sentiment Trajectory signal — LLM-based."""

from __future__ import annotations

import json

import anthropic

from ..models import Conversation, SignalName, SignalScore, Speaker, TurnSentiment
from .base import SignalComputer

SENTIMENT_PROMPT = """You are a contact center quality analyst evaluating the customer's emotional trajectory throughout a service conversation.

## Transcript
{transcript}

## Task
Analyze the customer's sentiment at each of their turns. Look for:
- Frustration spikes (sudden drops in sentiment)
- Recovery moments (agent successfully de-escalates)
- Overall trajectory (did sentiment improve, stay flat, or worsen?)

## Response Format
Return a JSON object with:
- "turn_scores": array of objects, one per CUSTOMER turn only, each with:
  - "turn_index": integer (0-indexed position in the full transcript)
  - "text": string (the customer's utterance, first 80 chars)
  - "score": float from -1.0 (very negative) to 1.0 (very positive), 0.0 = neutral
- "frustration_spikes": array of turn indices where sentiment dropped sharply
- "recovery_moments": array of turn indices where sentiment recovered after a drop
- "overall_delta": float — sentiment change from first to last customer turn
- "quality_score": float 0.0-1.0 — overall sentiment quality (1.0 = customer stayed happy throughout, 0.0 = customer was frustrated and never recovered)
- "reasoning": string (2-3 sentences summarizing the sentiment arc)

Return ONLY the JSON object, no other text."""


class SentimentSignal(SignalComputer):
    """Evaluates customer sentiment trajectory across the conversation."""

    def __init__(self, client: anthropic.AsyncAnthropic):
        self.client = client

    async def compute(self, conversation: Conversation) -> SignalScore:
        prompt = SENTIMENT_PROMPT.format(transcript=conversation.transcript_text)

        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            result = json.loads(text)
        except (json.JSONDecodeError, IndexError):
            return SignalScore(
                signal=SignalName.SENTIMENT,
                score=0.5,
                reasoning="Failed to parse LLM response.",
            )

        # Build per-turn sentiment list
        turn_sentiments = []
        for ts in result.get("turn_scores", []):
            turn_sentiments.append(TurnSentiment(
                turn_index=ts.get("turn_index", 0),
                speaker=Speaker.CUSTOMER,
                text=ts.get("text", ""),
                score=max(-1.0, min(1.0, float(ts.get("score", 0.0)))),
            ))

        # Build evidence from spikes and recoveries
        evidence = []
        for idx in result.get("frustration_spikes", []):
            matching = [ts for ts in turn_sentiments if ts.turn_index == idx]
            if matching:
                evidence.append(f"Frustration spike at turn {idx}: \"{matching[0].text}\"")
        for idx in result.get("recovery_moments", []):
            matching = [ts for ts in turn_sentiments if ts.turn_index == idx]
            if matching:
                evidence.append(f"Recovery at turn {idx}: \"{matching[0].text}\"")

        score = float(result.get("quality_score", 0.5))

        return SignalScore(
            signal=SignalName.SENTIMENT,
            score=round(max(0.0, min(1.0, score)), 3),
            reasoning=result.get("reasoning", ""),
            evidence=evidence,
            turn_sentiments=turn_sentiments,
        )
