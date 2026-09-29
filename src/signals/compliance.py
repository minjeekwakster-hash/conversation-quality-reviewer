"""Policy Compliance signal — hybrid (heuristic + LLM)."""

from __future__ import annotations

import json
from typing import Optional

import anthropic

from ..models import (
    ComplianceDetail,
    Conversation,
    SignalName,
    SignalScore,
)
from .base import SignalComputer

COMPLIANCE_LLM_PROMPT = """You are a contact center compliance analyst. An agent handled a customer service interaction. A heuristic system has already compared the agent's actions against the required procedure. Your job is to provide nuanced judgment on aspects the heuristic cannot capture.

## Conversation Context
- **Flow**: {flow} → {subflow}
- **Customer membership level**: {member_level}

## Expected Action Sequence (from knowledge base)
{expected_actions}

## Actual Actions Taken by Agent
{actual_actions}

## Heuristic Analysis
- Sequence match: {sequence_match}
- Missing actions: {missing_actions}
- Extra actions: {extra_actions}
- Heuristic score: {heuristic_score}

## Transcript
{transcript}

## Your Task
Evaluate nuanced compliance aspects the heuristic cannot capture:
1. Were any deviations JUSTIFIED? (e.g., customer already provided info, making a step unnecessary)
2. Did the agent correctly apply tier-based policies? (e.g., membership-level-specific return policies)
3. Did the agent verify identity appropriately?
4. Were there procedural shortcuts that were reasonable given context?

## Response Format
Return a JSON object with:
- "adjustment": float from -0.2 to 0.2 (positive = heuristic was too harsh, negative = heuristic was too lenient)
- "reasoning": string (2-3 sentences explaining the adjustment)
- "justified_deviations": array of strings describing any justified deviations
- "violations": array of strings describing any missed compliance issues

Return ONLY the JSON object, no other text."""


class ComplianceSignal(SignalComputer):
    """Hybrid compliance signal: heuristic action sequence matching + LLM nuance."""

    def __init__(
        self,
        kb: dict[str, list[str]],
        client: Optional[anthropic.AsyncAnthropic] = None,
        llm_enabled: bool = True,
    ):
        self.kb = kb  # subflow -> expected action sequence
        self.client = client
        self.llm_enabled = llm_enabled and client is not None

    def _heuristic_score(self, conversation: Conversation) -> ComplianceDetail:
        """Compare actual actions against expected sequence from kb.json."""
        subflow = conversation.scenario.subflow
        expected = self.kb.get(subflow, [])
        actual = conversation.actions_taken

        if not expected:
            return ComplianceDetail(
                expected_actions=expected,
                actual_actions=actual,
                heuristic_score=0.5,  # Can't assess without expected sequence
            )

        # Check for missing and extra actions
        expected_set = set(expected)
        actual_set = set(actual)
        missing = [a for a in expected if a not in actual_set]
        extra = [a for a in actual if a not in expected_set]

        # Check sequence ordering (for actions that are present)
        common_expected = [a for a in expected if a in actual_set]
        common_actual = [a for a in actual if a in expected_set]
        # Remove duplicates while preserving order
        seen = set()
        common_actual_dedup = []
        for a in common_actual:
            if a not in seen:
                seen.add(a)
                common_actual_dedup.append(a)

        sequence_match = common_actual_dedup == common_expected

        # Score components
        # 1. Completeness: what fraction of expected actions were performed?
        completeness = (len(expected) - len(missing)) / len(expected) if expected else 1.0

        # 2. Precision: what fraction of actual actions were expected?
        precision = (len(actual) - len(extra)) / len(actual) if actual else 0.5

        # 3. Order bonus
        order_bonus = 0.1 if sequence_match else 0.0

        # Weighted combination
        score = completeness * 0.5 + precision * 0.3 + order_bonus + 0.1  # base
        score = max(0.0, min(1.0, score))

        return ComplianceDetail(
            expected_actions=expected,
            actual_actions=actual,
            missing_actions=missing,
            extra_actions=extra,
            sequence_match=sequence_match,
            heuristic_score=round(score, 3),
        )

    async def compute(self, conversation: Conversation) -> SignalScore:
        detail = self._heuristic_score(conversation)

        evidence = []
        if detail.missing_actions:
            evidence.append(f"Missing actions: {', '.join(detail.missing_actions)}")
        if detail.extra_actions:
            evidence.append(f"Extra actions: {', '.join(detail.extra_actions)}")
        if detail.sequence_match:
            evidence.append("Action sequence matches expected order")
        else:
            evidence.append("Action sequence does not match expected order")

        # LLM adjustment layer
        if self.llm_enabled:
            try:
                adjustment_result = await self._llm_adjust(conversation, detail)
                detail.llm_adjustment = adjustment_result["adjustment"]
                reasoning = adjustment_result["reasoning"]
                if adjustment_result.get("justified_deviations"):
                    evidence.extend(
                        f"Justified: {d}" for d in adjustment_result["justified_deviations"]
                    )
                if adjustment_result.get("violations"):
                    evidence.extend(
                        f"Violation: {v}" for v in adjustment_result["violations"]
                    )
            except Exception:
                reasoning = "LLM adjustment failed; using heuristic score only."
                detail.llm_adjustment = 0.0
        else:
            reasoning = "Heuristic-only compliance score (LLM adjustment disabled)."

        final_score = max(0.0, min(1.0, detail.heuristic_score + detail.llm_adjustment))

        return SignalScore(
            signal=SignalName.COMPLIANCE,
            score=round(final_score, 3),
            reasoning=reasoning,
            evidence=evidence,
            compliance_detail=detail,
        )

    async def _llm_adjust(self, conversation: Conversation, detail: ComplianceDetail) -> dict:
        prompt = COMPLIANCE_LLM_PROMPT.format(
            flow=conversation.scenario.flow,
            subflow=conversation.scenario.subflow,
            member_level=conversation.scenario.personal.member_level,
            expected_actions=", ".join(detail.expected_actions) or "None specified",
            actual_actions=", ".join(detail.actual_actions) or "None recorded",
            sequence_match="Yes" if detail.sequence_match else "No",
            missing_actions=", ".join(detail.missing_actions) or "None",
            extra_actions=", ".join(detail.extra_actions) or "None",
            heuristic_score=detail.heuristic_score,
            transcript=conversation.transcript_text,
        )

        response = await self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(text)

        # Clamp adjustment to ±0.2
        adj = float(result.get("adjustment", 0.0))
        result["adjustment"] = max(-0.2, min(0.2, adj))
        return result
