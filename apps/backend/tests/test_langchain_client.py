"""Tests for LangChain OpenRouter adapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm.langchain_client import complete_structured, get_chat_model
from llm.schemas import SearchQueries


def test_get_chat_model_returns_none_without_api_key():
    with patch("llm.langchain_client.get_settings") as mock_settings:
        mock_settings.return_value.openrouter_api_key = ""
        mock_settings.return_value.chat_model = "openai/gpt-4o-mini"
        assert get_chat_model() is None


def test_get_chat_model_returns_client_with_api_key():
    with patch("llm.langchain_client.get_settings") as mock_settings:
        mock_settings.return_value.openrouter_api_key = "sk-test"
        mock_settings.return_value.chat_model = "openai/gpt-4o-mini"
        with patch("llm.langchain_client.ChatOpenAI") as mock_cls:
            mock_cls.return_value = MagicMock()
            client = get_chat_model("anthropic/claude-sonnet-4")
    mock_cls.assert_called_once()
    call_kwargs = mock_cls.call_args.kwargs
    assert call_kwargs["api_key"] == "sk-test"
    assert call_kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert call_kwargs["model"] == "anthropic/claude-sonnet-4"
    assert client is not None


@pytest.mark.asyncio
async def test_complete_structured_returns_none_when_no_client():
    with patch("llm.langchain_client.get_chat_model", return_value=None):
        result = await complete_structured("system", "user", SearchQueries)
    assert result is None


@pytest.mark.asyncio
async def test_complete_structured_returns_pydantic_instance():
    expected = SearchQueries(
        queries=["enterprise pilot risks", "startup SMB focus", "reference customer B2B"]
    )
    mock_structured = MagicMock()
    mock_structured.ainvoke = AsyncMock(return_value=expected)
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("llm.langchain_client.get_chat_model", return_value=mock_llm):
        result = await complete_structured("system", "user", SearchQueries)

    assert result == expected
    mock_llm.with_structured_output.assert_called_once_with(
        SearchQueries, method="json_schema"
    )


@pytest.mark.asyncio
async def test_complete_structured_validates_dict_response():
    mock_structured = MagicMock()
    mock_structured.ainvoke = AsyncMock(
        return_value={
            "queries": [
                "enterprise pilot case study",
                "startup sales motion focus",
                "B2B reference customer risk",
            ]
        }
    )
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    with patch("llm.langchain_client.get_chat_model", return_value=mock_llm):
        result = await complete_structured("system", "user", SearchQueries)

    assert result is not None
    assert len(result.queries) == 3
