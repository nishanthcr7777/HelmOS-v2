import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import MemoryChunk
from llm.openrouter import embed_text

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    id: str
    content: str
    summary: str | None
    chunk_type: str
    source_url: str | None
    score: float


@dataclass
class MemorySearchResult:
    chunks: list[RetrievedChunk]
    retrieved_chunks_count: int
    vector_hits: int
    text_hits: int
    used_vector: bool
    used_text_fallback: bool
    used_recent_fallback: bool


class MemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(
        self,
        query: str,
        workspace_id: str,
        project_id: str | None = None,
        limit: int = 10,
    ) -> MemorySearchResult:
        vector_hits = 0
        text_hits = 0
        used_vector = False
        used_text_fallback = False
        used_recent_fallback = False
        chunks: list[RetrievedChunk] = []

        embedding = await embed_text(query)
        if embedding:
            chunks = await self._vector_search(embedding, workspace_id, project_id, limit)
            vector_hits = len(chunks)
            used_vector = vector_hits > 0

        if not chunks:
            chunks = await self._text_fallback(query, workspace_id, project_id, limit)
            text_hits = len(chunks)
            used_text_fallback = text_hits > 0

        if not chunks:
            chunks = await self._recent_chunks_fallback(workspace_id, project_id, limit)
            used_recent_fallback = len(chunks) > 0

        logger.info(
            "memory_search workspace=%s retrieved_chunks_count=%d vector_hits=%d text_hits=%d "
            "used_text_fallback=%s used_recent_fallback=%s",
            workspace_id,
            len(chunks),
            vector_hits,
            text_hits,
            used_text_fallback,
            used_recent_fallback,
        )

        return MemorySearchResult(
            chunks=chunks,
            retrieved_chunks_count=len(chunks),
            vector_hits=vector_hits,
            text_hits=text_hits,
            used_vector=used_vector,
            used_text_fallback=used_text_fallback,
            used_recent_fallback=used_recent_fallback,
        )

    async def _vector_search(
        self,
        embedding: list[float],
        workspace_id: str,
        project_id: str | None,
        limit: int,
    ) -> list[RetrievedChunk]:
        vec = "[" + ",".join(str(x) for x in embedding) + "]"
        sql = """
            SELECT id, content, summary, chunk_type, source_url, created_at,
                   (1 - (embedding <=> CAST(:q AS vector))) AS similarity
            FROM memory_chunks
            WHERE workspace_id = :ws AND embedding IS NOT NULL
        """
        params: dict = {"q": vec, "ws": workspace_id, "lim": limit * 2}
        if project_id:
            sql += " AND project_id = :pid"
            params["pid"] = project_id
        sql += " ORDER BY embedding <=> CAST(:q AS vector) LIMIT :lim"

        rows = (await self.session.execute(text(sql), params)).mappings().all()
        scored: list[RetrievedChunk] = []
        now = datetime.now(timezone.utc)
        for row in rows:
            created = row["created_at"]
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_days = max(0, (now - created).days)
            recency = max(0.0, 1.0 - age_days / 90.0)
            sim = float(row["similarity"] or 0)
            score = sim * 0.7 + recency * 0.3
            scored.append(
                RetrievedChunk(
                    id=str(row["id"]),
                    content=row["content"],
                    summary=row["summary"],
                    chunk_type=row["chunk_type"],
                    source_url=row["source_url"],
                    score=score,
                )
            )
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[: min(8, limit)]

    async def _text_fallback(
        self,
        query: str,
        workspace_id: str,
        project_id: str | None,
        limit: int,
    ) -> list[RetrievedChunk]:
        q = select(MemoryChunk).where(MemoryChunk.workspace_id == workspace_id)
        if project_id:
            q = q.where(MemoryChunk.project_id == project_id)
        if query.strip():
            q = q.where(MemoryChunk.content.ilike(f"%{query[:200]}%"))
        q = q.order_by(MemoryChunk.created_at.desc()).limit(limit)
        result = await self.session.execute(q)
        return [
            RetrievedChunk(
                id=str(row.id),
                content=row.content,
                summary=row.summary,
                chunk_type=row.chunk_type,
                source_url=row.source_url,
                score=0.5,
            )
            for row in result.scalars().all()
        ]

    async def _recent_chunks_fallback(
        self,
        workspace_id: str,
        project_id: str | None,
        limit: int,
    ) -> list[RetrievedChunk]:
        q = select(MemoryChunk).where(MemoryChunk.workspace_id == workspace_id)
        if project_id:
            q = q.where(MemoryChunk.project_id == project_id)
        q = q.order_by(MemoryChunk.created_at.desc()).limit(limit)
        result = await self.session.execute(q)
        return [
            RetrievedChunk(
                id=str(row.id),
                content=row.content,
                summary=row.summary,
                chunk_type=row.chunk_type,
                source_url=row.source_url,
                score=0.3,
            )
            for row in result.scalars().all()
        ]
