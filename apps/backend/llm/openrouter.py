from collections.abc import AsyncIterator

import httpx
from openai import AsyncOpenAI

from config import get_settings


def _client() -> AsyncOpenAI | None:
    settings = get_settings()
    if not settings.openrouter_api_key:
        return None
    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )


async def embed_text(text: str) -> list[float] | None:
    client = _client()
    if client is None:
        return None
    settings = get_settings()
    resp = await client.embeddings.create(model=settings.embedding_model, input=text[:8000])
    return list(resp.data[0].embedding)


async def stream_chat_completion(
    system: str,
    user: str,
    model: str | None = None,
) -> AsyncIterator[str]:
    settings = get_settings()
    client = _client()
    if client is None:
        # Offline fallback for local dev without keys
        fallback = (
            "HelmOS is running without OPENROUTER_API_KEY. "
            "Configure keys and Supabase to enable grounded responses.\n\n"
            f"Your question: {user[:500]}"
        )
        for word in fallback.split(" "):
            yield word + " "
        return

    stream = await client.chat.completions.create(
        model=model or settings.chat_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def complete_json(system: str, user: str, model: str | None = None) -> str:
    client = _client()
    if client is None:
        return "{}"
    settings = get_settings()
    resp = await client.chat.completions.create(
        model=model or settings.chat_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or "{}"


async def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    async with httpx.AsyncClient(timeout=30.0) as http:
        r = await http.post(
            "https://api.tavily.com/search",
            json={"api_key": settings.tavily_api_key, "query": query, "max_results": max_results},
        )
        r.raise_for_status()
        return r.json().get("results", [])


async def firecrawl_scrape(url: str) -> str:
    settings = get_settings()
    if not settings.firecrawl_api_key:
        return ""
    async with httpx.AsyncClient(timeout=60.0) as http:
        r = await http.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
            json={"url": url, "formats": ["markdown"]},
        )
        if r.status_code >= 400:
            return ""
        data = r.json()
        md = data.get("data", {}).get("markdown") or data.get("markdown") or ""
        return md[:12000]
