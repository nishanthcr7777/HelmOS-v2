"""Tests for LangGraph research subgraph."""

from unittest.mock import AsyncMock, patch

import pytest

from research.board_evidence import EvidencePacket


@pytest.mark.asyncio
async def test_research_graph_no_tavily_key_short_circuits():
    from orchestrator.graphs.research_graph import research_graph

    packet = EvidencePacket(
        skipped_reason="TAVILY_API_KEY not configured",
        retrieval_case="none",
    )

    with patch(
        "orchestrator.graphs.research_graph.init_evidence_packet",
        new=AsyncMock(return_value=packet),
    ):
        result = await research_graph.ainvoke(
            {
                "question": "Should we pursue Acme?",
                "workspace_id": "clawback-labs",
                "workspace_context": "",
            },
            config={"configurable": {"session": AsyncMock()}},
        )

    trace = result["research_trace"]
    assert trace["retrieval_case"] == "none"
    assert trace["skipped_reason"] == "TAVILY_API_KEY not configured"
    assert result["packet"].tavily_hits == 0


@pytest.mark.asyncio
async def test_research_graph_no_relevant_path():
    from orchestrator.graphs.research_graph import research_graph

    packet = EvidencePacket(queries=["enterprise pilot startup"])

    async def _fake_init(_session, _workspace_id):
        return EvidencePacket()

    async def _fake_queries(p, _question, _ctx):
        p.queries = ["enterprise pilot startup"]
        return p

    async def _fake_tavily(p):
        p.tavily_hits = 5
        return p, [{"url": "https://example.com/a", "title": "a", "content": "x"}]

    async def _fake_filter(p, _question, _all_results):
        p.tavily_hits = 5
        p.relevant_hits = 0
        p.retrieval_case = "no_relevant"
        p.passed_to_researcher = 0
        p.text = "5 sources retrieved. 0 judged relevant."
        return p, []

    with (
        patch("orchestrator.graphs.research_graph.init_evidence_packet", side_effect=_fake_init),
        patch("orchestrator.graphs.research_graph.step_generate_queries", side_effect=_fake_queries),
        patch("orchestrator.graphs.research_graph.step_tavily_search", side_effect=_fake_tavily),
        patch("orchestrator.graphs.research_graph.step_filter_relevant", side_effect=_fake_filter),
        patch("orchestrator.graphs.research_graph.record_spend", new=AsyncMock()),
    ):
        result = await research_graph.ainvoke(
            {
                "question": "enterprise pilot?",
                "workspace_id": "clawback-labs",
                "workspace_context": "",
            },
            config={"configurable": {"session": AsyncMock()}},
        )

    assert result["research_trace"]["retrieval_case"] == "no_relevant"
    assert result["research_trace"]["tavily_hits"] == 5
    assert result["research_trace"]["relevant_hits"] == 0


@pytest.mark.asyncio
async def test_research_graph_trace_keys_match_packet():
    from orchestrator.graphs.research_graph import research_graph

    async def _fake_init(_session, _workspace_id):
        return EvidencePacket()

    async def _fake_queries(p, _question, _ctx):
        p.queries = ["q1"]
        return p

    async def _fake_tavily(p):
        p.tavily_hits = 2
        return p, [
            {
                "url": "https://saas.blog/enterprise-pilot",
                "title": "Enterprise pilot guide",
                "content": "B2B startup enterprise pilot reference customer strategy",
                "_relevance_score": 0.5,
            }
        ]

    async def _fake_filter(p, _question, all_results):
        p.relevant_hits = 1
        p.retrieval_case = "has_relevant"
        return p, all_results

    async def _fake_enrich(_session, p, _question, relevant_raw):
        p.passed_to_researcher = len(relevant_raw)
        p.items = []
        p.text = "packet text"
        p.research_tokens = 10
        return p

    with (
        patch("orchestrator.graphs.research_graph.init_evidence_packet", side_effect=_fake_init),
        patch("orchestrator.graphs.research_graph.step_generate_queries", side_effect=_fake_queries),
        patch("orchestrator.graphs.research_graph.step_tavily_search", side_effect=_fake_tavily),
        patch("orchestrator.graphs.research_graph.step_filter_relevant", side_effect=_fake_filter),
        patch("orchestrator.graphs.research_graph.step_enrich_and_summarize", side_effect=_fake_enrich),
        patch("orchestrator.graphs.research_graph.record_spend", new=AsyncMock()),
    ):
        result = await research_graph.ainvoke(
            {
                "question": "enterprise pilot startup",
                "workspace_id": "clawback-labs",
                "workspace_context": "ICP mid-market",
            },
            config={"configurable": {"session": AsyncMock()}},
        )

    trace = result["research_trace"]
    for key in (
        "tavily_hits",
        "relevant_hits",
        "passed_to_researcher",
        "research_tokens",
        "retrieval_case",
        "queries",
    ):
        assert key in trace
    assert trace["retrieval_case"] == "has_relevant"
