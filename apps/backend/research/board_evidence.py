"""Fresh external research for board sessions — query gen, Tavily, relevance filter."""

import json
import logging
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from core.spend import check_spend_cap, record_spend
from llm.openrouter import complete_json, firecrawl_scrape, tavily_search
from research.query_generator import generate_research_queries
from research.relevance import filter_relevant_results

logger = logging.getLogger(__name__)

_MAX_TAVILY_RAW = 20
_MAX_RELEVANT = 5


@dataclass
class EvidenceItem:
    url: str
    title: str
    snippet: str
    published_date: str | None
    summary: str
    relevance_score: float = 0.0
    extract: str | None = None


@dataclass
class EvidencePacket:
    items: list[EvidenceItem] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    text: str = ""
    source_count: int = 0
    tavily_hits: int = 0
    relevant_hits: int = 0
    passed_to_researcher: int = 0
    research_tokens: int = 0
    firecrawl_pages: int = 0
    skipped_reason: str | None = None
    retrieval_case: str = "none"  # none | no_sources | no_relevant | has_relevant

    def to_trace(self) -> dict:
        return {
            "tavily_hits": self.tavily_hits,
            "relevant_hits": self.relevant_hits,
            "passed_to_researcher": self.passed_to_researcher,
            "research_tokens": self.research_tokens,
            "research_sources_count": self.passed_to_researcher,
            "firecrawl_pages": self.firecrawl_pages,
            "queries": self.queries,
            "skipped_reason": self.skipped_reason,
            "retrieval_case": self.retrieval_case,
            "source_urls": [i.url for i in self.items if i.url],
        }


def _format_packet_text(items: list[EvidenceItem], header: str = "") -> str:
    if not items:
        return header or "No external research sources were retrieved for this question."
    lines = []
    if header:
        lines.append(header)
    for i, item in enumerate(items, 1):
        block = [
            f"### Source {i}: {item.title or 'Untitled'}",
            f"URL: {item.url}",
            f"Relevance: {item.relevance_score:.2f}",
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
    workspace_context: str = "",
) -> EvidencePacket:
    settings = get_settings()
    packet = EvidencePacket()

    if not settings.tavily_api_key:
        packet.skipped_reason = "TAVILY_API_KEY not configured"
        packet.retrieval_case = "none"
        packet.text = _format_packet_text([])
        logger.info("board_evidence skipped workspace=%s reason=no_tavily_key", workspace_id)
        return packet

    if not await check_spend_cap(session, "board_research", 0.15):
        packet.skipped_reason = "Daily spend cap exceeded"
        packet.retrieval_case = "none"
        packet.text = _format_packet_text([])
        return packet

    packet.queries = await generate_research_queries(question, workspace_context)

    all_results: list[dict] = []
    seen_urls: set[str] = set()
    for q in packet.queries:
        if not q.strip():
            continue
        for r in await tavily_search(q, max_results=4):
            url = (r.get("url") or "").strip()
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)
            if len(all_results) >= _MAX_TAVILY_RAW:
                break
        if len(all_results) >= _MAX_TAVILY_RAW:
            break

    await record_spend(session, "board_research", 0.04)
    packet.tavily_hits = len(all_results)

    if packet.tavily_hits == 0:
        packet.retrieval_case = "no_sources"
        packet.text = "No external sources found."
        return packet

    relevant_raw, relevant_count = filter_relevant_results(
        question, packet.queries, all_results, max_keep=_MAX_RELEVANT
    )
    packet.relevant_hits = relevant_count

    if not relevant_raw:
        packet.retrieval_case = "no_relevant"
        packet.passed_to_researcher = 0
        packet.source_count = 0
        packet.text = (
            f"{packet.tavily_hits} sources retrieved from Tavily. "
            f"0 judged relevant to the question. Evidence gap remains."
        )
        logger.info(
            "board_evidence workspace=%s tavily=%d relevant=0",
            workspace_id,
            packet.tavily_hits,
        )
        return packet

    packet.retrieval_case = "has_relevant"
    max_pages = min(settings.research_max_pages_per_session, 3)
    items: list[EvidenceItem] = []

    for r in relevant_raw:
        url = r.get("url", "")
        snippet = (r.get("content") or r.get("snippet") or "")[:500]
        title = r.get("title") or ""
        published = r.get("published_date") or r.get("date")
        rel = float(r.get("_relevance_score", 0))
        items.append(
            EvidenceItem(
                url=url,
                title=title,
                snippet=snippet,
                published_date=str(published) if published else None,
                summary=snippet[:300],
                relevance_score=rel,
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
                "Summarize each source into one factual sentence relevant to the founder question. "
                'Return JSON: {"summaries": [{"url": "...", "summary": "..."}]}',
                json.dumps(
                    {
                        "question": question[:500],
                        "sources": [
                            {"url": i.url, "title": i.title, "snippet": i.snippet} for i in items
                        ],
                    }
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
    packet.passed_to_researcher = len(items)
    packet.text = _format_packet_text(items)
    packet.research_tokens = len(packet.text) // 4

    logger.info(
        "board_evidence workspace=%s tavily=%d relevant=%d passed=%d tokens=%d",
        workspace_id,
        packet.tavily_hits,
        packet.relevant_hits,
        packet.passed_to_researcher,
        packet.research_tokens,
    )
    return packet
