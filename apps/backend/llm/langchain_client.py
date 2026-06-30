"""Thin LangChain adapter for OpenRouter chat + structured output."""

from typing import TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from config import get_settings

T = TypeVar("T", bound=BaseModel)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_chat_model(model: str | None = None) -> ChatOpenAI | None:
    settings = get_settings()
    if not settings.openrouter_api_key:
        return None
    return ChatOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=OPENROUTER_BASE_URL,
        model=model or settings.chat_model,
        temperature=0.2,
    )


async def complete_structured(
    system: str,
    user: str,
    schema: type[T],
    model: str | None = None,
) -> T | None:
    """Return a Pydantic instance or None when OpenRouter is unavailable."""
    llm = get_chat_model(model)
    if llm is None:
        return None
    structured = llm.with_structured_output(schema, method="json_schema")
    result = await structured.ainvoke(
        [SystemMessage(content=system), HumanMessage(content=user)]
    )
    if isinstance(result, BaseModel):
        return schema.model_validate(result.model_dump())
    if isinstance(result, dict):
        return schema.model_validate(result)
    return None
