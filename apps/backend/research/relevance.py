"""Score and filter Tavily results before building the evidence packet."""

import re
from urllib.parse import urlparse

# Domains that are almost never useful for founder board evidence
_NOISE_DOMAIN_PATTERNS = (
    "facebook.com",
    "fb.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "youtube.com",
    "youtu.be",
    "reddit.com",
    "quora.com",
    "justanswer.com",
    "answers.yahoo.com",
    "pinterest.com",
)

# Generic directory/list pages — low signal
_LOW_SIGNAL_PATH_PATTERNS = (
    "/fortune500",
    "/fortune-500",
    "/lists/",
    "/directory",
)

# Boost domains likely to carry analysis
_QUALITY_DOMAIN_HINTS = (
    "blog",
    "case-study",
    "casestudy",
    "research",
    "analysis",
    "harvard",
    "hbr.org",
    "gartner",
    "forbes.com",
    "techcrunch",
    "saas",
    "substack",
    "medium.com",
)


def _tokenize(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[a-zA-Z]{4,}", text)}


def _is_noise_url(url: str) -> bool:
    if not url:
        return True
    try:
        host = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
    except Exception:
        return True
    if any(p in host for p in _NOISE_DOMAIN_PATTERNS):
        return True
    if any(p in path for p in _LOW_SIGNAL_PATH_PATTERNS):
        return True
    # Generic Fortune 500 listicles without article depth
    if "fortune-500-companies" in path or host.endswith("50pros.com"):
        return True
    return False


def score_result(
    question: str,
    queries: list[str],
    result: dict,
) -> float:
    """Higher = more relevant. Returns 0.0 for hard-rejected noise."""
    url = (result.get("url") or "").strip()
    if _is_noise_url(url):
        return 0.0

    title = result.get("title") or ""
    snippet = result.get("content") or result.get("snippet") or ""
    blob = f"{title} {snippet} {url}".lower()

    q_tokens = _tokenize(question)
    query_tokens: set[str] = set()
    for q in queries:
        query_tokens |= _tokenize(q)

    overlap_q = len(q_tokens & _tokenize(blob)) / max(len(q_tokens), 1)
    overlap_queries = len(query_tokens & _tokenize(blob)) / max(len(query_tokens), 1)

    score = overlap_q * 0.35 + overlap_queries * 0.45

    # Domain quality boost
    host = urlparse(url).netloc.lower()
    if any(h in host or h in blob for h in _QUALITY_DOMAIN_HINTS):
        score += 0.15

    # Penalize very short snippets (thin pages)
    if len(snippet.strip()) < 80:
        score -= 0.1

    # Slight boost for case study / pilot / enterprise keywords in blob
    strategic_terms = {
        "enterprise",
        "pilot",
        "case study",
        "reference customer",
        "startup",
        "smb",
        "procurement",
        "founder",
        "b2b",
        "saas",
        "distraction",
        "focus",
    }
    hits = sum(1 for t in strategic_terms if t in blob)
    score += min(0.2, hits * 0.04)

    return max(0.0, min(1.0, score))


def filter_relevant_results(
    question: str,
    queries: list[str],
    results: list[dict],
    *,
    min_score: float = 0.12,
    max_keep: int = 5,
) -> tuple[list[dict], int]:
    """
    Return (scored_results_sorted, relevant_count).
    Each result dict gets '_relevance_score' attached.
    """
    scored: list[tuple[float, dict]] = []
    for r in results:
        s = score_result(question, queries, r)
        if s >= min_score:
            r = {**r, "_relevance_score": s}
            scored.append((s, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    kept = [r for _, r in scored[:max_keep]]
    return kept, len(scored)
