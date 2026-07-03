"""Tests for board evidence pipeline steps."""

from unittest.mock import AsyncMock, patch

import pytest

from research.board_evidence import (
    EvidenceItem,
    EvidencePacket,
    gather_board_evidence,
    init_evidence_packet,
    step_filter_relevant,
    step_generate_queries,
    step_tavily_search,
)


def test_evidence_packet_to_trace_includes_debug_keys():
    packet = EvidencePacket(
        queries=["q1", "q2"],
        tavily_hits=5,
        relevant_hits=2,
        passed_to_researcher=2,
        research_tokens=100,
        retrieval_case="has_relevant",
        items=[EvidenceItem(url="https://example.com", title="T", snippet="s", published_date=None, summary="sum")],
    )
    trace = packet.to_trace()
    assert trace["tavily_hits"] == 5
    assert trace["relevant_hits"] == 2
    assert trace["passed_to_researcher"] == 2
    assert trace["retrieval_case"] == "has_relevant"
    assert trace["queries"] == ["q1", "q2"]
    assert trace["source_urls"] == ["https://example.com"]


@pytest.mark.asyncio
async def test_init_evidence_packet_skips_without_tavily_key():
    session = AsyncMock()
    with patch("research.board_evidence.get_settings") as mock_settings:
        mock_settings.return_value.tavily_api_key = ""
        packet = await init_evidence_packet(session, "clawback-labs")

    assert packet.skipped_reason == "TAVILY_API_KEY not configured"
    assert packet.retrieval_case == "none"


@pytest.mark.asyncio
async def test_init_evidence_packet_skips_when_spend_cap_exceeded():
    session = AsyncMock()
    with patch("research.board_evidence.get_settings") as mock_settings:
        mock_settings.return_value.tavily_api_key = "tvly-test"
        with patch(
            "research.board_evidence.check_spend_cap",
            new=AsyncMock(return_value=False),
        ):
            packet = await init_evidence_packet(session, "clawback-labs")

    assert packet.skipped_reason == "Daily spend cap exceeded"
    assert packet.retrieval_case == "none"


@pytest.mark.asyncio
async def test_step_filter_relevant_no_sources():
    packet = EvidencePacket(tavily_hits=0)
    updated, relevant = await step_filter_relevant(packet, "question?", [])

    assert updated.retrieval_case == "no_sources"
    assert updated.text == "No external sources found."
    assert relevant == []


@pytest.mark.asyncio
async def test_step_tavily_search_dedupes_urls():
    packet = EvidencePacket(queries=["enterprise pilot"])
    tavily_results = [
        {"url": "https://example.com/a", "title": "A", "content": "x"},
        {"url": "https://example.com/a", "title": "A dup", "content": "y"},
        {"url": "https://example.com/b", "title": "B", "content": "z"},
    ]

    with patch(
        "research.board_evidence.tavily_search",
        new=AsyncMock(return_value=tavily_results),
    ):
        updated, all_results = await step_tavily_search(packet)

    assert updated.tavily_hits == 2
    assert len(all_results) == 2


@pytest.mark.asyncio
async def test_gather_board_evidence_no_relevant_path():
    session = AsyncMock()

    async def _fake_init(_session, _workspace_id):
        return EvidencePacket()

    async def _fake_queries(packet, _question, _ctx):
        packet.queries = ["enterprise pilot startup"]
        return packet

    async def _fake_tavily(packet):
        packet.tavily_hits = 4
        return packet, [
            {"url": "https://facebook.com/x", "title": "noise", "content": "enterprise"}
        ]

    with (
        patch("research.board_evidence.init_evidence_packet", side_effect=_fake_init),
        patch("research.board_evidence.step_generate_queries", side_effect=_fake_queries),
        patch("research.board_evidence.step_tavily_search", side_effect=_fake_tavily),
        patch("research.board_evidence.record_spend", new=AsyncMock()),
    ):
        packet = await gather_board_evidence(
            session, "enterprise pilot?", "clawback-labs", workspace_context=""
        )

    assert packet.tavily_hits == 4
    assert packet.retrieval_case in ("no_relevant", "no_sources")
