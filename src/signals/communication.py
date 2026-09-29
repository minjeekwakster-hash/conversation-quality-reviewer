"""Agent Communication Quality signal — LLM-based."""

from __future__ import annotations

import json

import anthropic

from ..models import (
    CommunicationSubScores,
    Conversation,
    SignalName,
    SignalScore,
)
from .base import SignalComputer

COMMUNICATION_PROMPT = """You are a contact center quality analyst evaluating the agent's communication quality in a customer service conversation.

## Transcript
{transcript}

## Evaluation Dimensions
Score each dimension from 0.0 to 1.0:

1. **Clarity** (0-1): Are the agent's responses clear, specific, and easy to understand? Do they avoid jargon? Do they provide concrete next steps?

2. **Empathy** (0-1): Does the agent acknowledge the customer's feelings? Do they use empathetic language? Do they show understanding of the customer's situation?

3. **Professionalism** (0-1): Is the tone appropriate? Does the agent maintain composure? Are responses well-structured and grammatically correct?

4. **Proactiveness** (0-1): Does the agent anticipate needs? Do they offer additional help? Do they provide information before being asked?

## Response Format
Return a JSON object with:
- "clarity": float 0.0-1.0
- "empathy": float 0.0-1.0
- "professionalism": float 0.0-1.0
- "proactiveness": float 0.0-1.0
- "overall_score": float 0.0-1.0 (weighted average — clarity 0.3, empathy 0.3, professionalism 0.2, proactiveness 0.2)
- "reasoning": string (2-3 sentences summarizing communication quality)
- "flagged_utterances": array of objects with "text" (agent utterance, first 80 chars) and "issue" (what's wrong) for any problematic agent responses
- "strengths": array of 1-2 strings noting what the agent did well

Return ONLY the JSON object, no other text."""


class CommunicationSignal(SignalComputer):
    """Evaluates agent communication quality across 4 sub-dimensions."""

    def __init__(self, client: anthropic.AsyncAnthropic):
        self.client = client

    async def compute(self, conversation: Conversation) -> SignalScore:
        prompt = COMMUNICATION_PROMPT.format(transcript=conversation.transcript_text)

        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            result = json.loads(text)
        except (json.JSONDecodeError, IndexError):
            return SignalScore(
                signal=SignalName.COMMUNICATION,
                score=0.5,
                reasoning="Failed to parse LLM response.",
            )

        sub_scores = CommunicationSubScores(
            clarity=max(0.0, min(1.0, float(result.get("clarity", 0.5)))),
            empathy=max(0.0, min(1.0, float(result.get("empathy", 0.5)))),
            professionalism=max(0.0, min(1.0, float(result.get("professionalism", 0.5)))),
            proactiveness=max(0.0, min(1.0, float(result.get("proactiveness", 0.5)))),
        )

        score = float(result.get("overall_score", 0.5))

        flagged = [
            f"{f.get('text', '')}: {f.get('issue', '')}"
            for f in result.get("flagged_utterances", [])
        ]

        evidence = result.get("strengths", [])

        return SignalScore(
            signal=SignalName.COMMUNICATION,
            score=round(max(0.0, min(1.0, score)), 3),
            reasoning=result.get("reasoning", ""),
            evidence=evidence,
            communication_sub=sub_scores,
            flagged_utterances=flagged,
        )
