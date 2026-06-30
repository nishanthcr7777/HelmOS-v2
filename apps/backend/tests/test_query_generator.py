"""Tests for LLM-powered research query generation."""

from unittest.mock import AsyncMock, patch

import pytest

from llm.schemas import SearchQueries
from research.query_generator import _fallback_queries, generate_research_queries


def test_fallback_queries_returns_three_to_five():
    queries = _fallback_queries("Should we pursue Acme Corp for Q3 outreach?")
    assert 3 <= len(queries) <= 5
    assert all(isinstance(q, str) and q.strip() for q in queries)


@pytest.mark.asyncio
async def test_generate_research_queries_uses_structured_output():
    structured = SearchQueries(
        queries=[
            "mid market payroll compliance hiring",
            "enterprise sales distraction startup",
            "B2B outreach ICP employee band",
        ]
    )
    with patch(
        "research.query_generator.complete_structured",
        new=AsyncMock(return_value=structured),
    ):
        queries = await generate_research_queries("Should we target Acme Corp?")

    assert len(queries) == 3
    assert "mid market payroll" in queries[0]


@pytest.mark.asyncio
async def test_generate_research_queries_falls_back_to_legacy_json():
    with patch(
        "research.query_generator.complete_structured",
        new=AsyncMock(return_value=None),
    ):
        with patch(
            "research.query_generator.complete_json",
            new=AsyncMock(
                return_value='{"queries": ["q one", "q two", "q three"]}'
            ),
        ):
            queries = await generate_research_queries("Enterprise pilot question?")

    assert queries == ["q one", "q two", "q three"]


@pytest.mark.asyncio
async def test_generate_research_queries_uses_heuristic_when_llm_fails():
    with patch(
        "research.query_generator.complete_structured",
        new=AsyncMock(return_value=None),
    ):
        with patch(
            "research.query_generator.complete_json",
            new=AsyncMock(return_value="not json"),
        ):
            queries = await generate_research_queries("Should startup accept enterprise pilot?")

    assert len(queries) >= 3
    assert any("startup" in q.lower() for q in queries)
