import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.spend import check_spend_cap, record_spend
from db.models import MemoryChunk, ResearchCache, ResearchJob
from llm.openrouter import complete_json, firecrawl_scrape, tavily_search


STEPS = ["querying", "searching", "extracting", "summarizing", "done"]


async def run_research_job(session: AsyncSession, job_id: uuid.UUID) -> None:
    result = await session.execute(select(ResearchJob).where(ResearchJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        return

    if not await check_spend_cap(session, "research", 0.15):
        job.status = "failed"
        job.error = "Daily spend cap exceeded"
        job.step = "done"
        await session.commit()
        return

    try:
        job.step = "querying"
        queries = [
            f"{job.entity_name} company overview",
            f"{job.entity_name} funding news compliance",
        ]
        job.queries = queries
        await session.flush()

        job.step = "searching"
        all_results: list[dict] = []
        for q in queries:
            all_results.extend(await tavily_search(q, max_results=5))
        await record_spend(session, "research", 0.05)
        await session.flush()

        sources: list[dict] = []
        for r in all_results[:8]:
            sources.append(
                {
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("content", r.get("snippet", ""))[:500],
                    "relevance": "relevant",
                }
            )
        job.sources = sources
        job.step = "extracting"
        await session.flush()

        extracted: list[str] = []
        for src in sources[:3]:
            url = src.get("url")
            if not url:
                continue
            cached = await session.execute(select(ResearchCache).where(ResearchCache.url == url))
            row = cached.scalar_one_or_none()
            if row and row.fetched_at > datetime.now(timezone.utc) - timedelta(days=7):
                extracted.append(row.content[:4000])
                continue
            content = await firecrawl_scrape(url)
            if content:
                if row:
                    row.content = content
                    row.fetched_at = datetime.now(timezone.utc)
                else:
                    session.add(ResearchCache(url=url, content=content))
                extracted.append(content[:4000])
        await record_spend(session, "research", 0.08)
        job.step = "summarizing"
        await session.flush()

        summary_raw = await complete_json(
            "Summarize research into key_facts list as JSON: { summaries: [{ key_facts, source_url }] }",
            str({"entity": job.entity_name, "sources": sources, "extracts": extracted[:3]})[:12000],
        )
        import json

        try:
            parsed = json.loads(summary_raw)
        except json.JSONDecodeError:
            parsed = {"summaries": []}

        for item in parsed.get("summaries", [])[:5]:
            session.add(
                MemoryChunk(
                    workspace_id=job.workspace_id,
                    chunk_type="research_summary",
                    content=item.get("key_facts", ""),
                    source_url=item.get("source_url"),
                    entity_name=job.entity_name,
                    fetched_at=datetime.now(timezone.utc),
                    metadata_={},
                )
            )

        job.step = "done"
        job.status = "complete"
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)[:500]
        job.step = "done"
    await session.flush()

