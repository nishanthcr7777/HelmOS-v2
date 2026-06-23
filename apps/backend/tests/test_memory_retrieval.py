import asyncio
from unittest.mock import AsyncMock, patch

from memory.retrieval import MemoryService, RetrievedChunk


def _chunk(cid: str = "c1") -> RetrievedChunk:
    return RetrievedChunk(
        id=cid,
        content="test content",
        summary=None,
        chunk_type="strategy_note",
        source_url=None,
        score=0.5,
    )


def test_vector_empty_falls_back_to_text():
    async def run():
        service = MemoryService(session=AsyncMock())  # type: ignore[arg-type]
        with (
            patch.object(service, "_vector_search", new_callable=AsyncMock, return_value=[]),
            patch.object(service, "_text_fallback", new_callable=AsyncMock, return_value=[_chunk()]),
            patch("memory.retrieval.embed_text", new_callable=AsyncMock, return_value=[0.1]),
        ):
            return await service.search("query", "ws-1", limit=8)

    result = asyncio.run(run())
    assert result.vector_hits == 0
    assert result.text_hits == 1
    assert result.used_text_fallback is True
    assert result.retrieved_chunks_count == 1


def test_vector_and_text_empty_falls_back_to_recent():
    async def run():
        service = MemoryService(session=AsyncMock())  # type: ignore[arg-type]
        with (
            patch.object(service, "_vector_search", new_callable=AsyncMock, return_value=[]),
            patch.object(service, "_text_fallback", new_callable=AsyncMock, return_value=[]),
            patch.object(
                service,
                "_recent_chunks_fallback",
                new_callable=AsyncMock,
                return_value=[_chunk("c2")],
            ),
            patch("memory.retrieval.embed_text", new_callable=AsyncMock, return_value=[0.1]),
        ):
            return await service.search("query", "ws-1", limit=8)

    result = asyncio.run(run())
    assert result.used_recent_fallback is True
    assert result.retrieved_chunks_count == 1
    assert result.chunks[0].id == "c2"


def test_no_embedding_uses_text_fallback():
    async def run():
        service = MemoryService(session=AsyncMock())  # type: ignore[arg-type]
        with (
            patch.object(service, "_text_fallback", new_callable=AsyncMock, return_value=[_chunk()]),
            patch("memory.retrieval.embed_text", new_callable=AsyncMock, return_value=None),
        ):
            return await service.search("query", "ws-1", limit=8)

    result = asyncio.run(run())
    assert result.used_vector is False
    assert result.text_hits == 1
