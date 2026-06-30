"""Tests for LangGraph board entry routing."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestrator.board import run_board_session


@pytest.mark.asyncio
async def test_run_board_session_uses_imperative_by_default():
    mock_board = MagicMock()
    with patch("orchestrator.board.get_settings") as mock_settings:
        mock_settings.return_value.use_langgraph_board = False
        with patch(
            "orchestrator.board._run_board_session_imperative",
            new=AsyncMock(return_value=mock_board),
        ) as imperative:
            with patch(
                "orchestrator.board.run_board_session_graph",
                new=AsyncMock(),
            ) as graph:
                result = await run_board_session(
                    AsyncMock(), "clawback-labs", "Test question?"
                )
    imperative.assert_awaited_once()
    graph.assert_not_awaited()
    assert result is mock_board


@pytest.mark.asyncio
async def test_run_board_session_uses_graph_when_flag_on():
    mock_board = MagicMock()
    with patch("orchestrator.board.get_settings") as mock_settings:
        mock_settings.return_value.use_langgraph_board = True
        with patch(
            "orchestrator.board.run_board_session_graph",
            new=AsyncMock(return_value=mock_board),
        ) as graph:
            with patch(
                "orchestrator.board._run_board_session_imperative",
                new=AsyncMock(),
            ) as imperative:
                result = await run_board_session(
                    AsyncMock(), "clawback-labs", "Test question?"
                )
    graph.assert_awaited_once()
    imperative.assert_not_awaited()
    assert result is mock_board
