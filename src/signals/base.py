"""Abstract base class for quality signals."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Conversation, SignalScore


class SignalComputer(ABC):
    """Base class for all quality signal computers."""

    @abstractmethod
    async def compute(self, conversation: Conversation) -> SignalScore:
        """Compute the signal score for a conversation. Async for LLM-based signals."""
        ...
