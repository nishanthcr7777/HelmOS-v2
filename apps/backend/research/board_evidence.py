"""Fresh external research for board sessions — Tavily + optional Firecrawl."""

import json
import logging
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from core.spend import check_spend_cap, record_spend
from llm.openrouter import complete_json, firecrawl_scrape, tavily_search

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    url: str
    title: str
    snippet: str
    published_date: str | None
    summary: str
    extract: str | None = None


@dataclass
class EvidencePacket:
    items: list[EvidenceItem] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    text: str = ""
    source_count: int = 0
    tavily_hits: int = 0
    firecrawl_pages: int = 0
    skipped_reason: str | None = None

    def to_trace(self) -> dict:
        return {
            "research_sources_count": self.source_count,
            "tavily_hits": self.tavily_hits,
            "firecrawl_pages": self.firecrawl_pages,
            "queries": self.queries,
            "skipped_reason": self.skipped_reason,
            "source_urls": [i.url for i in self.items if i.url],
        }


def _format_packet_text(items: list[EvidenceItem]) -> str:
    if not items:
        return "No external research sources were retrieved for this question."
    lines = []
    for i, item in enumerate(items, 1):
        block = [
            f"### Source {i}: {item.title or 'Untitled'}",
            f"URL: {item.url}",
        ]
        if item.published_date:
            block.append(f"Published: {item.published_date}")
        if item.summary:
            block.append(f"Summary: {item.summary}")
        if item.snippet:
            block.append(f"Snippet: {item.snippet[:600]}")
        if item.extract:
            block.append(f"Extract: {item.extract[:1200]}")
        lines.append("\n".join(block))
    return "\n\n".join(lines)


async def gather_board_evidence(
    session: AsyncSession,
    question: str,
    workspace_id: str,
) -> EvidencePacket:
    settings = get_settings()
    packet = EvidencePacket()

    if not settings.tavily_api_key:
        packet.skipped_reason = "TAVILY_API_KEY not configured"
        packet.text = _format_packet_text([])
        logger.info("board_evidence skipped workspace=%s reason=no_tavily_key", workspace_id)
        return packet

    if not await check_spend_cap(session, "board_research", 0.12):
        packet.skipped_reason = "Daily spend cap exceeded"
        packet.text = _format_packet_text([])
        return packet

    queries = [
        question[:200],
        f"{question[:120]} market data facts",
    ]
    packet.queries = queries

    all_results: list[dict] = []
    for q in queries:
        if q.strip():
            all_results.extend(await tavily_search(q, max_results=4))
    await record_spend(session, "board_research", 0.04)
    packet.tavily_hits = len(all_results)

    seen_urls: set[str] = set()
    raw_sources: list[dict] = []
    for r in all_results:
        url = (r.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        raw_sources.append(r)
        if len(raw_sources) >= 8:
            break

    max_pages = min(settings.research_max_pages_per_session, 3)
    items: list[EvidenceItem] = []

    for r in raw_sources:
        url = r.get("url", "")
        snippet = (r.get("content") or r.get("snippet") or "")[:500]
        title = r.get("title") or ""
        published = r.get("published_date") or r.get("date")
        items.append(
            EvidenceItem(
                url=url,
                title=title,
                snippet=snippet,
                published_date=str(published) if published else None,
                summary=snippet[:300],
            )
        )

    if settings.firecrawl_api_key:
        for item in items[:max_pages]:
            if not item.url:
                continue
            extract = await firecrawl_scrape(item.url)
            if extract:
                item.extract = extract[:2000]
                packet.firecrawl_pages += 1
        if packet.firecrawl_pages:
            await record_spend(session, "board_research", 0.06)

    if items and settings.openrouter_api_key:
        try:
            summary_raw = await complete_json(
                "Summarize each source into one factual sentence. "
                'Return JSON: {"summaries": [{"url": "...", "summary": "..."}]}',
                json.dumps(
                    [{"url": i.url, "title": i.title, "snippet": i.snippet} for i in items[:6]]
                )[:8000],
            )
            parsed = json.loads(summary_raw)
            url_to_summary = {
                s.get("url", ""): s.get("summary", "") for s in parsed.get("summaries", [])
            }
            for item in items:
                if item.url in url_to_summary and url_to_summary[item.url]:
                    item.summary = url_to_summary[item.url]
        except (json.JSONDecodeError, TypeError):
            pass

    packet.items = items
    packet.source_count = len(items)
    packet.text = _format_packet_text(items)
    logger.info(
        "board_evidence workspace=%s sources=%d tavily=%d firecrawl=%d",
        workspace_id,
        packet.source_count,
        packet.tavily_hits,
        packet.firecrawl_pages,
    )
    return packet
