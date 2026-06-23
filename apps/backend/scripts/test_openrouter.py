import asyncio

from config import get_settings
from llm import openrouter

get_settings.cache_clear()


async def main() -> None:
    client = openrouter._client()
    print("client", bool(client))
    emb = await openrouter.embed_text("hello")
    print("embedding", emb is not None, len(emb) if emb else 0)
    parts: list[str] = []
    async for token in openrouter.stream_chat_completion("You are helpful.", "Say hi in three words."):
        parts.append(token)
    text = "".join(parts)
    print("stream", text[:200])
    if "running without OPENROUTER_API_KEY" in text:
        print("FAIL")
    else:
        print("PASS")


asyncio.run(main())
