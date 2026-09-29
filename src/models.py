"""Pydantic models for the Conversation Quality Reviewer."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- ABCD Dataset Models ---

class Speaker(str, Enum):
    AGENT = "agent"
    CUSTOMER = "customer"
    ACTION = "action"


class Turn(BaseModel):
    """A single turn in a conversation (from 'original')."""
    speaker: Speaker
    text: str


class DelexedTurn(BaseModel):
    """A delexicalized turn with ML task targets (from 'delexed')."""
    speaker: Speaker
    text: str
    turn_count: int
    targets: list  # [subflow, action_type, action_name, params, candidate_idx]
    candidates: list[int] = Field(default_factory=list)

    @property
    def subflow(self) -> str:
        return self.targets[0] if self.targets else ""

    @property
    def action_type(self) -> Optional[str]:
        return self.targets[1] if len(self.targets) > 1 else None

    @property
    def action_name(self) -> Optional[str]:
        return self.targets[2] if len(self.targets) > 2 else None

    @property
    def action_params(self) -> list:
        return self.targets[3] if len(self.targets) > 3 else []


class PersonalInfo(BaseModel):
    customer_name: str = ""
    email: str = ""
    member_level: str = ""
    phone: str = ""
    username: str = ""


class OrderInfo(BaseModel):
    street_address: str = ""
    full_address: str = ""
    city: str = ""
    num_products: str = ""
    order_id: str = ""
    packaging: str = ""
    payment_method: str = ""
    products: str = ""  # JSON string repr
    purchase_date: str = ""
    state: str = ""
    zip_code: str = ""


class ProductInfo(BaseModel):
    names: list[str] = Field(default_factory=list)
    amounts: list[float] = Field(default_factory=list)


class Scenario(BaseModel):
    personal: PersonalInfo = Field(default_factory=PersonalInfo)
    order: OrderInfo = Field(default_factory=OrderInfo)
    product: ProductInfo = Field(default_factory=ProductInfo)
    flow: str = ""
    subflow: str = ""


class Conversation(BaseModel):
    """A full ABCD conversation."""
    convo_id: int
    scenario: Scenario
    original: list[Turn]
    delexed: list[DelexedTurn] = Field(default_factory=list)

    @property
    def agent_turns(self) -> list[Turn]:
        return [t for t in self.original if t.speaker == Speaker.AGENT]

    @property
    def customer_turns(self) -> list[Turn]:
        return [t for t in self.original if t.speaker == Speaker.CUSTOMER]

    @property
    def action_turns(self) -> list[Turn]:
        return [t for t in self.original if t.speaker == Speaker.ACTION]

    @property
    def actions_taken(self) -> list[str]:
        """Extract ordered list of action names from delexed turns."""
        return [
            t.action_name
            for t in self.delexed
            if t.action_type == "take_action" and t.action_name
        ]

    @property
    def transcript_text(self) -> str:
        """Format conversation as readable transcript."""
        lines = []
        for t in self.original:
            label = t.speaker.value.upper()
            lines.append(f"[{label}]: {t.text}")
        return "\n".join(lines)


# --- Signal Scoring Models ---

class SignalName(str, Enum):
    RESOLUTION = "resolution"
    EFFICIENCY = "efficiency"
    COMPLIANCE = "compliance"
    SENTIMENT = "sentiment"
    COMMUNICATION = "communication"


SIGNAL_WEIGHTS = {
    SignalName.RESOLUTION: 0.30,
    SignalName.COMPLIANCE: 0.25,
    SignalName.EFFICIENCY: 0.15,
    SignalName.SENTIMENT: 0.15,
    SignalName.COMMUNICATION: 0.15,
}


class TurnSentiment(BaseModel):
    """Per-turn sentiment score for the sentiment signal."""
    turn_index: int
    speaker: Speaker
    text: str
    score: float = Field(ge=-1.0, le=1.0)  # -1 negative, 0 neutral, 1 positive


class CommunicationSubScores(BaseModel):
    """Sub-dimension scores for agent communication quality."""
    clarity: float = Field(ge=0.0, le=1.0)
    empathy: float = Field(ge=0.0, le=1.0)
    professionalism: float = Field(ge=0.0, le=1.0)
    proactiveness: float = Field(ge=0.0, le=1.0)


class ComplianceDetail(BaseModel):
    """Details for the compliance signal."""
    expected_actions: list[str] = Field(default_factory=list)
    actual_actions: list[str] = Field(default_factory=list)
    missing_actions: list[str] = Field(default_factory=list)
    extra_actions: list[str] = Field(default_factory=list)
    sequence_match: bool = False
    heuristic_score: float = Field(ge=0.0, le=1.0, default=0.5)
    llm_adjustment: float = Field(ge=-0.2, le=0.2, default=0.0)


class SignalScore(BaseModel):
    """Score for a single quality signal on a single conversation."""
    signal: SignalName
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    evidence: list[str] = Field(default_factory=list)
    # Signal-specific detail fields (optional)
    turn_sentiments: Optional[list[TurnSentiment]] = None
    communication_sub: Optional[CommunicationSubScores] = None
    compliance_detail: Optional[ComplianceDetail] = None
    flagged_utterances: list[str] = Field(default_factory=list)


class ConversationResult(BaseModel):
    """Complete scoring result for one conversation."""
    convo_id: int
    flow: str = ""
    subflow: str = ""
    scores: dict[str, SignalScore] = Field(default_factory=dict)
    overall_score: float = 0.0
    flags: list[str] = Field(default_factory=list)
    scored_at: Optional[datetime] = None

    def compute_overall(self) -> float:
        total = 0.0
        weight_sum = 0.0
        for signal_name, weight in SIGNAL_WEIGHTS.items():
            if signal_name.value in self.scores:
                total += self.scores[signal_name.value].score * weight
                weight_sum += weight
        self.overall_score = total / weight_sum if weight_sum > 0 else 0.0
        return self.overall_score


class BatchResult(BaseModel):
    """Results for a batch of conversations."""
    batch_id: str
    total: int = 0
    completed: int = 0
    results: list[ConversationResult] = Field(default_factory=list)
    status: str = "pending"  # pending, running, completed


class BatchSummary(BaseModel):
    """Aggregate summary statistics for a batch."""
    total_conversations: int = 0
    avg_overall: float = 0.0
    avg_by_signal: dict[str, float] = Field(default_factory=dict)
    avg_by_flow: dict[str, float] = Field(default_factory=dict)
    score_distribution: dict[str, int] = Field(default_factory=dict)  # bucket -> count
    flagged_count: int = 0
