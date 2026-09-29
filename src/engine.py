"""Signal orchestrator — runs all 5 signals with async concurrency and caching."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

import anthropic

from .ingest import load_kb
from .models import (
    BatchResult,
    BatchSummary,
    Conversation,
    ConversationResult,
    SignalName,
)
from .signals.communication import CommunicationSignal
from .signals.compliance import ComplianceSignal
from .signals.efficiency import EfficiencySignal
from .signals.resolution import ResolutionSignal
from .signals.sentiment import SentimentSignal


class ScoringEngine:
    """Orchestrates all quality signals with concurrency control and caching."""

    def __init__(
        self,
        anthropic_client: Optional[anthropic.AsyncAnthropic] = None,
        baselines: Optional[dict] = None,
        kb: Optional[dict] = None,
        max_concurrent: int = 5,
        llm_enabled: bool = True,
    ):
        self.client = anthropic_client
        self.llm_enabled = llm_enabled and self.client is not None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._cache: dict[int, ConversationResult] = {}

        # Initialize signals
        self.efficiency = EfficiencySignal(baselines=baselines)

        if self.llm_enabled:
            self.resolution = ResolutionSignal(self.client)
            self.sentiment = SentimentSignal(self.client)
            self.communication = CommunicationSignal(self.client)
            self.compliance = ComplianceSignal(
                kb=kb or {},
                client=self.client,
                llm_enabled=True,
            )
        else:
            self.compliance = ComplianceSignal(
                kb=kb or {},
                client=None,
                llm_enabled=False,
            )

    async def score_conversation(
        self,
        conversation: Conversation,
        use_cache: bool = True,
    ) -> ConversationResult:
        """Score a single conversation across all signals."""
        if use_cache and conversation.convo_id in self._cache:
            return self._cache[conversation.convo_id]

        result = ConversationResult(
            convo_id=conversation.convo_id,
            flow=conversation.scenario.flow,
            subflow=conversation.scenario.subflow,
        )

        # Always run heuristic signals (instant)
        efficiency_score = await self.efficiency.compute(conversation)
        result.scores[SignalName.EFFICIENCY.value] = efficiency_score

        # Compliance heuristic runs regardless; LLM layer is conditional
        compliance_score = await self.compliance.compute(conversation)
        result.scores[SignalName.COMPLIANCE.value] = compliance_score

        # Run LLM signals concurrently if enabled
        if self.llm_enabled:
            async def _run_with_semaphore(signal, convo):
                async with self.semaphore:
                    return await signal.compute(convo)

            llm_tasks = [
                _run_with_semaphore(self.resolution, conversation),
                _run_with_semaphore(self.sentiment, conversation),
                _run_with_semaphore(self.communication, conversation),
            ]
            llm_results = await asyncio.gather(*llm_tasks, return_exceptions=True)

            for r in llm_results:
                if isinstance(r, Exception):
                    continue
                result.scores[r.signal.value] = r

        # Compute overall score, flags, and timestamp
        result.compute_overall()
        result.flags = self._compute_flags(result)
        result.scored_at = datetime.now(timezone.utc)

        self._cache[conversation.convo_id] = result
        return result

    async def score_batch(
        self,
        conversations: list[Conversation],
        batch_id: str = "default",
        on_progress: Optional[callable] = None,
    ) -> BatchResult:
        """Score a batch of conversations."""
        batch = BatchResult(
            batch_id=batch_id,
            total=len(conversations),
            status="running",
        )

        for i, convo in enumerate(conversations):
            try:
                result = await self.score_conversation(convo)
                batch.results.append(result)
                batch.completed = i + 1
                if on_progress:
                    on_progress(batch)
            except Exception as e:
                # Log error but continue with remaining conversations
                print(f"Error scoring convo {convo.convo_id}: {e}")
                batch.completed = i + 1

        batch.status = "completed"
        return batch

    def summarize(self, batch: BatchResult) -> BatchSummary:
        """Compute aggregate statistics for a batch."""
        results = batch.results
        if not results:
            return BatchSummary()

        n = len(results)

        # Avg overall
        avg_overall = sum(r.overall_score for r in results) / n

        # Avg by signal
        avg_by_signal = {}
        for signal in SignalName:
            scores = [
                r.scores[signal.value].score
                for r in results
                if signal.value in r.scores
            ]
            if scores:
                avg_by_signal[signal.value] = round(sum(scores) / len(scores), 3)

        # Avg by flow
        from collections import defaultdict
        flow_scores = defaultdict(list)
        for r in results:
            flow_scores[r.flow].append(r.overall_score)
        avg_by_flow = {
            flow: round(sum(s) / len(s), 3) for flow, s in flow_scores.items()
        }

        # Score distribution (10 buckets)
        distribution = {f"{i/10:.1f}-{(i+1)/10:.1f}": 0 for i in range(10)}
        for r in results:
            bucket_idx = min(int(r.overall_score * 10), 9)
            key = f"{bucket_idx/10:.1f}-{(bucket_idx+1)/10:.1f}"
            distribution[key] += 1

        flagged_count = sum(1 for r in results if r.flags)

        return BatchSummary(
            total_conversations=n,
            avg_overall=round(avg_overall, 3),
            avg_by_signal=avg_by_signal,
            avg_by_flow=avg_by_flow,
            score_distribution=distribution,
            flagged_count=flagged_count,
        )

    @staticmethod
    def _compute_flags(result: ConversationResult) -> list[str]:
        """Flag conversations that need attention."""
        flags = []

        # Low overall score
        if result.overall_score < 0.4:
            flags.append("low_overall_score")

        # Check individual signals
        for signal_name, score_obj in result.scores.items():
            if score_obj.score < 0.3:
                flags.append(f"low_{signal_name}")

        # Resolution failure
        if (
            SignalName.RESOLUTION.value in result.scores
            and result.scores[SignalName.RESOLUTION.value].score < 0.5
        ):
            flags.append("resolution_failure")

        # Compliance violation
        if (
            SignalName.COMPLIANCE.value in result.scores
            and result.scores[SignalName.COMPLIANCE.value].score < 0.5
        ):
            flags.append("compliance_violation")

        # Communication issues (flagged utterances)
        comm = result.scores.get(SignalName.COMMUNICATION.value)
        if comm and comm.flagged_utterances:
            flags.append("communication_issues")

        # Sentiment drop
        sentiment = result.scores.get(SignalName.SENTIMENT.value)
        if sentiment and sentiment.turn_sentiments:
            scores = [ts.score for ts in sentiment.turn_sentiments]
            if len(scores) >= 2 and scores[-1] - scores[0] < -0.5:
                flags.append("sentiment_deterioration")

        return flags
