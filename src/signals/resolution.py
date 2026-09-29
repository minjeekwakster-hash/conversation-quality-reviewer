"""Resolution Effectiveness signal — LLM-based."""

from __future__ import annotations

import json

import anthropic

from ..models import Conversation, SignalName, SignalScore
from .base import SignalComputer

RESOLUTION_PROMPT = """You are a contact center quality analyst evaluating whether a customer service agent successfully resolved the customer's issue.

## Conversation Context
- **Customer Issue**: {flow} → {subflow}
- **Customer**: {customer_name} ({member_level} member)
- **Order**: {order_id} — {products}

## Transcript
{transcript}

## Actions Taken by Agent
{actions}

## Evaluation Criteria
1. **Issue Identified**: Did the agent correctly understand what the customer needed?
2. **Steps Completed**: Did the agent take the necessary actions to address the issue?
3. **Outcome Achieved**: Was the customer's issue actually resolved by the end?
4. **Customer Confirmation**: Did the customer acknowledge the resolution?

## Response Format
Return a JSON object with:
- "score": float 0.0-1.0 (0=unresolved, 0.5=partial, 1.0=fully resolved)
- "reasoning": string explaining the score (2-3 sentences)
- "evidence": array of 1-3 direct quotes from the transcript supporting the score
- "issue_identified": boolean
- "steps_completed": boolean
- "outcome_achieved": boolean

Return ONLY the JSON object, no other text."""


class ResolutionSignal(SignalComputer):
    """Evaluates whether the agent resolved the customer's issue."""

    def __init__(self, client: anthropic.AsyncAnthropic):
        self.client = client

    async def compute(self, conversation: Conversation) -> SignalScore:
        scenario = conversation.scenario
        products = scenario.product.names if scenario.product.names else "N/A"

        prompt = RESOLUTION_PROMPT.format(
            flow=scenario.flow,
            subflow=scenario.subflow,
            customer_name=scenario.personal.customer_name,
            member_level=scenario.personal.member_level,
            order_id=scenario.order.order_id or "N/A",
            products=", ".join(products) if isinstance(products, list) else products,
            transcript=conversation.transcript_text,
            actions=", ".join(conversation.actions_taken) or "None recorded",
        )

        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            text = response.content[0].text.strip()
            # Handle markdown-wrapped JSON
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            result = json.loads(text)
        except (json.JSONDecodeError, IndexError):
            return SignalScore(
                signal=SignalName.RESOLUTION,
                score=0.5,
                reasoning="Failed to parse LLM response.",
                evidence=[],
            )

        return SignalScore(
            signal=SignalName.RESOLUTION,
            score=round(max(0.0, min(1.0, float(result.get("score", 0.5)))), 3),
            reasoning=result.get("reasoning", ""),
            evidence=result.get("evidence", []),
        )
