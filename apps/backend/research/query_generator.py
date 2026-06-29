"""Generate focused Tavily search queries from a founder board question."""

import json
import logging
import re

from llm.openrouter import complete_json

logger = logging.getLogger(__name__)

_MAX_QUERIES = 5
_MIN_QUERIES = 3


def _fallback_queries(question: str) -> list[str]:
    """Heuristic queries when LLM is unavailable."""
    text = re.sub(r"\s+", " ", question.strip())[:400]
    # Strip bullet noise for keyword extraction
    words = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", text)]
    key = " ".join(words[:8]) if words else text[:80]

    return [
        f"startup {key} B2B strategy",
        f"enterprise pilot customer benefits risks startup",
        f"startup SMB vs enterprise sales focus early stage",
        f"reference customer impact B2B SaaS sales",
        f"enterprise deal distraction startup founder",
    ][:_MAX_QUERIES]


async def generate_research_queries(question: str, workspace_context: str = "") -> list[str]:
    """
    Produce 3-5 focused search queries. Never pass the raw founder question to Tavily.
    """
    system = """You generate web search queries for a founder intelligence board.
Given a strategic question, output 3-5 SHORT search queries (4-10 words each).

Rules:
- Do NOT copy the founder question verbatim
- Focus on facts, market dynamics, risks, case studies, industry analysis
- Queries must be searchable (no bullets, no company-specific deal terms unless generic)
- Cover: benefits, risks, comparable cases, strategic tradeoffs

Return JSON only: {"queries": ["query one", "query two", ...]}"""

    user = f"Question:\n{question[:1500]}"
    if workspace_context.strip():
        user += f"\n\nWorkspace context:\n{workspace_context[:800]}"

    try:
        raw = await complete_json(system, user)
        parsed = json.loads(raw)
        queries = parsed.get("queries", [])
        if isinstance(queries, list):
            cleaned = [str(q).strip() for q in queries if str(q).strip()][: _MAX_QUERIES]
            if len(cleaned) >= _MIN_QUERIES:
                logger.info("research_queries generated=%d", len(cleaned))
                return cleaned
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("research_queries llm_failed: %s", exc)

    fallback = _fallback_queries(question)
    logger.info("research_queries using_fallback count=%d", len(fallback))
    return fallback
