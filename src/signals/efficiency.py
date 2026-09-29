"""Conversation Efficiency signal — pure heuristic, no LLM calls."""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from ..models import Conversation, SignalName, SignalScore, Speaker
from .base import SignalComputer


class EfficiencySignal(SignalComputer):
    """Measures conversation efficiency via turn count, substantive ratio, and action efficiency.

    Pure heuristic — runs instantly with no API calls.
    """

    def __init__(self, baselines: Optional[dict[str, dict]] = None):
        # Per-subflow baselines: {subflow: {avg_turns, avg_actions, ...}}
        self.baselines = baselines or {}

    @classmethod
    def compute_baselines(cls, conversations: list[Conversation]) -> dict[str, dict]:
        """Pre-compute per-subflow baselines from the full dataset."""
        by_subflow: dict[str, list[dict]] = defaultdict(list)

        for c in conversations:
            stats = cls._conversation_stats(c)
            by_subflow[c.scenario.subflow].append(stats)

        baselines = {}
        for subflow, stats_list in by_subflow.items():
            n = len(stats_list)
            baselines[subflow] = {
                "avg_turns": sum(s["total_turns"] for s in stats_list) / n,
                "avg_agent_turns": sum(s["agent_turns"] for s in stats_list) / n,
                "avg_customer_turns": sum(s["customer_turns"] for s in stats_list) / n,
                "avg_actions": sum(s["action_count"] for s in stats_list) / n,
                "count": n,
            }
        return baselines

    @staticmethod
    def _conversation_stats(c: Conversation) -> dict:
        agent_turns = [t for t in c.original if t.speaker == Speaker.AGENT]
        customer_turns = [t for t in c.original if t.speaker == Speaker.CUSTOMER]
        action_turns = [t for t in c.original if t.speaker == Speaker.ACTION]

        # Substantive turns: non-trivial utterances (>10 chars, not just greetings)
        filler_phrases = {
            "hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye",
            "ok", "okay", "sure", "yes", "no", "alright", "great",
            "is there anything else i can help you with?",
            "is there anything else i can help with?",
            "no that's all", "no that's it", "no thanks",
        }
        substantive_agent = sum(
            1 for t in agent_turns
            if len(t.text) > 10 and t.text.lower().strip().rstrip("!?.") not in filler_phrases
        )

        return {
            "total_turns": len(c.original),
            "agent_turns": len(agent_turns),
            "customer_turns": len(customer_turns),
            "action_count": len(action_turns),
            "substantive_agent": substantive_agent,
        }

    async def compute(self, conversation: Conversation) -> SignalScore:
        stats = self._conversation_stats(conversation)
        subflow = conversation.scenario.subflow
        baseline = self.baselines.get(subflow)

        evidence = []
        sub_scores = []

        # 1. Turn efficiency vs. baseline
        if baseline and baseline["avg_turns"] > 0:
            turn_ratio = stats["total_turns"] / baseline["avg_turns"]
            # Score: 1.0 if at or below average, decreasing as turns increase
            if turn_ratio <= 1.0:
                turn_score = 1.0
            elif turn_ratio <= 1.5:
                turn_score = 1.0 - (turn_ratio - 1.0)  # Linear decay
            else:
                turn_score = max(0.2, 1.0 - (turn_ratio - 1.0) * 0.8)
            sub_scores.append(turn_score)
            evidence.append(
                f"Turn count: {stats['total_turns']} vs. subflow avg {baseline['avg_turns']:.0f} "
                f"(ratio: {turn_ratio:.2f})"
            )
        else:
            # No baseline — use absolute thresholds
            total = stats["total_turns"]
            if total <= 15:
                turn_score = 1.0
            elif total <= 25:
                turn_score = 0.8
            elif total <= 40:
                turn_score = 0.6
            else:
                turn_score = 0.4
            sub_scores.append(turn_score)
            evidence.append(f"Turn count: {total} (no subflow baseline)")

        # 2. Substantive turn ratio (agent)
        if stats["agent_turns"] > 0:
            substantive_ratio = stats["substantive_agent"] / stats["agent_turns"]
            sub_scores.append(substantive_ratio)
            evidence.append(
                f"Substantive agent turns: {stats['substantive_agent']}/{stats['agent_turns']} "
                f"({substantive_ratio:.0%})"
            )

        # 3. Agent-to-customer turn ratio (ideally near 1:1, penalize agent-heavy)
        if stats["customer_turns"] > 0:
            ac_ratio = stats["agent_turns"] / stats["customer_turns"]
            if 0.8 <= ac_ratio <= 1.3:
                ratio_score = 1.0
            elif ac_ratio < 0.8:
                ratio_score = max(0.5, ac_ratio)
            else:
                ratio_score = max(0.4, 1.0 - (ac_ratio - 1.3) * 0.5)
            sub_scores.append(ratio_score)
            evidence.append(f"Agent:Customer turn ratio: {ac_ratio:.2f}")

        # 4. Action efficiency vs. baseline
        if baseline and baseline["avg_actions"] > 0:
            action_ratio = stats["action_count"] / baseline["avg_actions"]
            if 0.8 <= action_ratio <= 1.2:
                action_score = 1.0
            elif action_ratio < 0.8:
                action_score = 0.7  # Too few actions might mean steps skipped
            else:
                action_score = max(0.4, 1.0 - (action_ratio - 1.2) * 0.5)
            sub_scores.append(action_score)
            evidence.append(
                f"Actions taken: {stats['action_count']} vs. subflow avg {baseline['avg_actions']:.0f}"
            )

        # Weighted average of sub-scores
        final_score = sum(sub_scores) / len(sub_scores) if sub_scores else 0.5

        # Build reasoning
        if final_score >= 0.8:
            reasoning = "Conversation was handled efficiently."
        elif final_score >= 0.6:
            reasoning = "Conversation efficiency was acceptable but could be improved."
        else:
            reasoning = "Conversation was notably inefficient."

        return SignalScore(
            signal=SignalName.EFFICIENCY,
            score=round(max(0.0, min(1.0, final_score)), 3),
            reasoning=reasoning,
            evidence=evidence,
        )
