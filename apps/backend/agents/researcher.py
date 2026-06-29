import json
from typing import Any

from agents.base import _as_float, _as_str_list
from agents.board_modes import BoardMode, enforce_agent_output
from llm.agent_models import resolve_board_agent_model
from llm.openrouter import complete_json
from research.board_evidence import EvidencePacket

RESEARCHER_SYSTEM = """You are the Researcher on a founder intelligence board.

You may only use supplied evidence in the evidence packet.

Do not speculate.

If evidence is insufficient, explicitly say so in evidence_gaps.

Your job is not to recommend strategy.
Your job is not to plan execution.

Your job is to report what evidence supports and what evidence contradicts.

For EACH supplied source you must either:
- cite it in evidence_for or evidence_against (with URL in parentheses), OR
- explain in evidence_gaps why it does not answer the question

Respond in JSON only with keys:
agent, question_answered, verdict, confidence, influence_weight, evidence_quality,
research_age_days, evidence_score, evidence_used, evidence_for, evidence_against,
evidence_gaps, key_assumptions, risks, unknowns, primary_pick, recommendation,
suggested_next_action.

verdict: for|against|conditional
confidence and evidence_score: floats 0.0-1.0
evidence_for: list of factual claims WITH source URL in parentheses
evidence_against: list of factual claims WITH source URL in parentheses
evidence_gaps: list of what is NOT evidenced
recommendation: evidence report only — NOT strategy advice
influence_weight should be 0.4.
agent must be "researcher".
"""


def _build_fallback_recommendation(
    evidence: EvidencePacket,
    evidence_for: list[str],
    evidence_against: list[str],
    evidence_gaps: list[str],
) -> str:
    case = evidence.retrieval_case

    if case == "none" or evidence.skipped_reason:
        reason = evidence.skipped_reason or "research unavailable"
        return f"No external sources found ({reason})."

    if case == "no_sources" or evidence.tavily_hits == 0:
        return "No external sources found."

    if case == "no_relevant":
        return (
            f"{evidence.tavily_hits} sources retrieved. "
            f"0 judged relevant. Evidence gap remains."
        )

    # has_relevant — build from lists or explain gap
    for_part = "; ".join(evidence_for[:3])
    against_part = "; ".join(evidence_against[:3])
    gaps_part = "; ".join(evidence_gaps[:3])

    if not for_part and not against_part:
        gaps_part = gaps_part or (
            f"Sources passed ({evidence.passed_to_researcher}) but none directly "
            "address the question — review URLs in evidence packet."
        )
        return (
            f"{evidence.tavily_hits} sources retrieved. "
            f"{evidence.passed_to_researcher} passed relevance filter. "
            f"Evidence for: none on-topic. Evidence against: none on-topic. Gaps: {gaps_part}"
        )

    return (
        f"Evidence for: {for_part or 'none on-topic'}. "
        f"Evidence against: {against_part or 'none on-topic'}. "
        f"Gaps: {gaps_part or 'see evidence packet'}."
    )


def _default_evidence_gaps(evidence: EvidencePacket) -> list[str]:
    if evidence.retrieval_case == "no_sources":
        return ["No external web sources returned from search."]
    if evidence.retrieval_case == "no_relevant":
        return [
            f"{evidence.tavily_hits} Tavily results returned; none met relevance threshold.",
            "Evidence gap remains for this question.",
        ]
    if evidence.passed_to_researcher == 0:
        return ["No relevant sources passed to researcher."]
    return []


async def run_researcher_agent(
    question: str,
    evidence: EvidencePacket,
    board_mode: BoardMode = "decision",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Returns (agent_output, researcher_debug_trace).
    Debug trace contains raw_response and parsed_response.
    """
    model = resolve_board_agent_model("researcher")
    user = f"""Question: {question}

## External research evidence packet
Retrieval: tavily_hits={evidence.tavily_hits}, relevant_hits={evidence.relevant_hits}, passed={evidence.passed_to_researcher}

{evidence.text[:14000]}
"""
    raw = await complete_json(RESEARCHER_SYSTEM, user, model=model)
    parse_error: str | None = None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        data = {}
        parse_error = str(exc)

    debug_trace = {
        "raw_response": raw[:20000] if raw else "",
        "parsed_response": dict(data),
        "parse_error": parse_error,
        "model": model,
    }

    data.setdefault("agent", "researcher")
    data.setdefault("question_answered", question)
    data["confidence"] = _as_float(data.get("confidence"), 0.5)
    data["influence_weight"] = _as_float(data.get("influence_weight"), 0.4)
    data.setdefault("evidence_quality", "moderate")
    data["research_age_days"] = 0

    default_score = 0.1
    if evidence.retrieval_case == "has_relevant" and evidence.passed_to_researcher > 0:
        default_score = 0.35
    elif evidence.tavily_hits > 0:
        default_score = 0.15
    data["evidence_score"] = _as_float(data.get("evidence_score"), default_score)

    data["evidence_for"] = _as_str_list(data.get("evidence_for", []))
    data["evidence_against"] = _as_str_list(data.get("evidence_against", []))
    data["evidence_gaps"] = _as_str_list(data.get("evidence_gaps", []))

    if not data["evidence_gaps"]:
        data["evidence_gaps"] = _default_evidence_gaps(evidence)

    # Always populate evidence_used from packet when we have items
    if evidence.items:
        data["evidence_used"] = [
            {
                "source": item.url,
                "snippet": item.summary or item.snippet,
                "url": item.url,
                "relevance_score": item.relevance_score,
            }
            for item in evidence.items[:6]
        ]
    else:
        data["evidence_used"] = []

    data["key_assumptions"] = _as_str_list(data.get("key_assumptions", []))
    data["risks"] = _as_str_list(data.get("risks", []))
    data["unknowns"] = _as_str_list(data.get("unknowns", [])) or data["evidence_gaps"]

    rec = str(data.get("recommendation") or "").strip()
    if not rec or rec.lower().startswith("evidence for: none cited"):
        data["recommendation"] = _build_fallback_recommendation(
            evidence,
            data["evidence_for"],
            data["evidence_against"],
            data["evidence_gaps"],
        )

    data.setdefault("primary_pick", "evidence report")
    data.setdefault(
        "suggested_next_action",
        "Close top evidence gap with one targeted source"
        if evidence.retrieval_case != "has_relevant"
        else "Validate top evidence claim against primary source",
    )
    data.setdefault("verdict", "conditional" if board_mode == "decision" else "needs_research")

    output = enforce_agent_output(data, board_mode)
    debug_trace["parsed_response"] = dict(output)
    return output, debug_trace
