"""Tests for individual LangGraph board nodes."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestrator.graphs.board_graph import node_gather_research, node_run_agents
from research.board_evidence import EvidencePacket


@pytest.mark.asyncio
async def test_node_gather_research_merges_trace_into_context():
    packet = EvidencePacket(
        tavily_hits=3,
        relevant_hits=1,
        passed_to_researcher=1,
        retrieval_case="has_relevant",
    )
    research_result = {"packet": packet, "research_trace": packet.to_trace()}

    with patch(
        "orchestrator.graphs.board_graph.research_graph.ainvoke",
        new=AsyncMock(return_value=research_result),
    ):
        result = await node_gather_research(
            {
                "question": "Enterprise pilot?",
                "workspace_id": "clawback-labs",
                "board_ctx_text": "ICP mid-market",
                "board_ctx_trace": {"beliefs_count": 4},
            },
            {"configurable": {"session": AsyncMock()}},
        )

    assert result["evidence_packet"].tavily_hits == 3
    assert result["board_ctx_trace"]["research"]["retrieval_case"] == "has_relevant"
    assert result["board_ctx_trace"]["research_sources_count"] == 1


@pytest.mark.asyncio
async def test_node_run_agents_invokes_all_roles():
    researcher_out = {"agent": "researcher", "verdict": "conditional"}

    async def _fake_researcher(*_args, **_kwargs):
        return researcher_out, {"raw_response": "{}"}

    async def _fake_agent(agent_key, *_args, **_kwargs):
        return {"agent": agent_key, "verdict": "conditional"}

    with patch(
        "orchestrator.graphs.board_graph.run_researcher_agent",
        new=AsyncMock(side_effect=_fake_researcher),
    ):
        with patch(
            "orchestrator.graphs.board_graph.run_agent",
            new=AsyncMock(side_effect=_fake_agent),
        ):
            result = await node_run_agents(
                {
                    "question": "Test?",
                    "board_mode": "decision",
                    "beliefs_block": "ICP = mid-market",
                    "board_ctx_text": "context",
                    "evidence_packet": EvidencePacket(),
                },
                {"configurable": {"session": MagicMock()}},
            )

    assert len(result["agent_outputs"]) == 5
    agents = {o["agent"] for o in result["agent_outputs"]}
    assert agents == {"cto", "operator", "skeptic", "researcher", "sales_strategist"}
