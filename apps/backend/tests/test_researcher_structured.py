"""Tests for researcher agent structured LLM output."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.researcher import run_researcher_agent
from llm.schemas import ResearcherLLMOutput
from research.board_evidence import EvidencePacket


@pytest.mark.asyncio
async def test_researcher_uses_structured_output():
    evidence = EvidencePacket(
        tavily_hits=3,
        relevant_hits=2,
        passed_to_researcher=2,
        retrieval_case="has_relevant",
        text="### Source 1: Example\nURL: https://example.com",
        items=[],
    )
    structured = ResearcherLLMOutput(
        question_answered="Should we pursue Acme?",
        verdict="conditional",
        confidence=0.7,
        evidence_for=["Series B funding signal (https://example.com)"],
        evidence_against=[],
        evidence_gaps=["No payroll clawback signal"],
        recommendation="Evidence for: Series B funding.",
    )

    with patch(
        "agents.researcher.complete_structured",
        new=AsyncMock(return_value=structured),
    ):
        with patch(
            "agents.researcher.resolve_board_agent_model",
            return_value="anthropic/claude-sonnet-4",
        ):
            output, debug = await run_researcher_agent(
                "Should we pursue Acme?", evidence, board_mode="decision"
            )

    assert output["agent"] == "researcher"
    assert output["verdict"] in ("conditional", "lean_for", "lean_against", "needs_research")
    assert debug["parse_error"] is None
    assert "Series B" in debug["raw_response"]


@pytest.mark.asyncio
async def test_researcher_falls_back_to_complete_json():
    evidence = EvidencePacket(
        tavily_hits=0,
        retrieval_case="no_sources",
        text="No external sources found.",
    )
    legacy_payload = {
        "agent": "researcher",
        "verdict": "conditional",
        "confidence": 0.4,
        "evidence_for": [],
        "evidence_against": [],
        "evidence_gaps": ["No sources"],
        "recommendation": "No external sources found.",
    }

    with patch("agents.researcher.complete_structured", new=AsyncMock(return_value=None)):
        with patch(
            "agents.researcher.complete_json",
            new=AsyncMock(return_value=json.dumps(legacy_payload)),
        ):
            with patch(
                "agents.researcher.resolve_board_agent_model",
                return_value="anthropic/claude-sonnet-4",
            ):
                output, debug = await run_researcher_agent(
                    "Test question?", evidence, board_mode="decision"
                )

    assert output["recommendation"] == "No external sources found."
    assert debug["parsed_response"]["agent"] == "researcher"
