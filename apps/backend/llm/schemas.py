"""Pydantic schemas for LangChain structured output."""

from pydantic import BaseModel, Field


class SearchQueries(BaseModel):
    queries: list[str] = Field(
        description="3-5 short web search queries (4-10 words each)"
    )


class EvidenceSummaryItem(BaseModel):
    url: str = ""
    summary: str = ""


class EvidenceSummaries(BaseModel):
    summaries: list[EvidenceSummaryItem] = Field(default_factory=list)


class ResearcherLLMOutput(BaseModel):
    """Structured researcher response — post-processed by run_researcher_agent."""

    agent: str = "researcher"
    question_answered: str = ""
    verdict: str = "conditional"
    confidence: float = 0.5
    influence_weight: float = 0.4
    evidence_quality: str = "moderate"
    research_age_days: int = 0
    evidence_score: float = 0.35
    evidence_used: list[dict] = Field(default_factory=list)
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    key_assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    primary_pick: str = "evidence report"
    recommendation: str = ""
    suggested_next_action: str = ""
