"""Typed contracts for everything the LLM produces and the pipeline consumes.

The LLM is forced to answer through tools whose input schemas are generated
from these models, and every response is validated against them before it is
used. If the model returns something malformed, the pipeline fails loudly
rather than putting a made-up number in front of leadership.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RAG(str, Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"

    @property
    def rank(self) -> int:
        return {"RED": 0, "AMBER": 1, "GREEN": 2}[self.value]


RiskCategory = Literal[
    "delivery", "data", "governance_compliance", "people_capacity",
    "financial", "technology", "adoption", "security",
]
MilestoneStatus = Literal["done", "on_track", "at_risk", "late", "tbc"]
DependencyStatus = Literal["blocking", "at_risk", "on_track"]


class Milestone(BaseModel):
    name: str = Field(description="Milestone name as written in the report, shortened if needed.")
    baseline: Optional[date] = Field(None, description="Originally planned date (ISO). Null if not stated.")
    forecast: Optional[date] = Field(None, description="Current forecast or actual date (ISO). Null if TBC.")
    status: MilestoneStatus


class Risk(BaseModel):
    title: str = Field(description="Short risk name, max ~8 words.")
    description: str = Field(description="One or two sentences: cause -> effect.")
    category: RiskCategory
    likelihood: int = Field(ge=1, le=5, description="1 = rare ... 5 = almost certain.")
    impact: int = Field(ge=1, le=5, description="1 = negligible ... 5 = severe, multi-initiative or €1M+.")
    mitigation: Optional[str] = None
    evidence: str = Field(description="A short verbatim quote (5-25 words) from the report that supports this risk.")


class Dependency(BaseModel):
    depends_on: str = Field(description="The other initiative, by ID if the report gives one, otherwise by name.")
    what: str = Field(description="What is needed from it.")
    needed_by: Optional[date] = None
    status: DependencyStatus


class InitiativeExtraction(BaseModel):
    """What the LLM pulls out of one status report."""

    initiative_id: str
    period_end: date
    reported_rag: RAG = Field(description="The RAG status the author gave.")
    assessed_rag: RAG = Field(description="Your independent RAG based on the evidence in the report.")
    rag_rationale: str = Field(description="One sentence; explain any gap between reported and assessed RAG.")
    percent_complete: Optional[int] = Field(None, ge=0, le=100)
    headline: str = Field(description="Leadership-ready one-liner, max 20 words.")
    progress: list[str] = Field(description="Up to 4 concrete achievements this period.")
    milestones: list[Milestone]
    risks: list[Risk]
    dependencies: list[Dependency]
    asks: list[str] = Field(description="Decisions or help requested from leadership.")


class PortfolioRisk(BaseModel):
    title: str = Field(description="Portfolio-level risk, max 10 words.")
    root_initiative: str = Field(description="Initiative ID where the root cause sits.")
    affected_initiatives: list[str] = Field(description="Initiative IDs whose delivery is hit, incl. the root.")
    linked_risk_ids: list[str] = Field(description="IDs of the initiative-level risks this rolls up (e.g. 'DAT-02.R1').")
    impact_statement: str = Field(description="What happens if unmanaged, quantified where the reports allow.")
    recommended_action: str = Field(description="Concrete action with owner and date where possible.")


class PortfolioSynthesis(BaseModel):
    """Cross-initiative view the LLM writes after reading every extraction."""

    headline: str = Field(description="One sentence, max 25 words, for the top of the slide.")
    key_messages: list[str] = Field(description="Exactly 3 messages for the speaker notes.")
    portfolio_risks: list[PortfolioRisk]
    decisions_required: list[str] = Field(description="Max 4 decisions leadership must take, each with a date.")


# ---------------------------------------------------------------- analysed

class ScoredRisk(BaseModel):
    risk_id: str
    initiative_id: str
    risk: Risk
    score: int
    direct_dependents: int
    portfolio_score: float
    grounded: bool


class RankedPortfolioRisk(BaseModel):
    rank: int
    risk: PortfolioRisk
    base_score: int
    portfolio_score: float
