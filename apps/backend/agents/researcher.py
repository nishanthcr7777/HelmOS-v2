import json
from typing import Any

from agents.base import _as_float, _as_str_list
from agents.board_modes import BoardMode, enforce_agent_output
from llm.agent_models import resolve_board_agent_model
from llm.openrouter import complete_json
from research.board_evidence import EvidencePacket

RESEARCHER_SYSTEM = """You are the Researcher on a founder intelligence board.

You may only use supplied evidence.

Do not speculate.

If evidence is insufficient, explicitly say so.

Your job is not to recommend strategy.
Your job is not to plan execution.

Your job is to report what evidence supports and what evidence contradicts.

Respond in JSON only with keys:
agent, question_answered, verdict, confidence, influence_weight, evidence_quality,
research_age_days, evidence_score, evidence_used, evidence_for, evidence_against,
evidence_gaps, key_assumptions, risks, unknowns, primary_pick, recommendation,
suggested_next_action.

verdict: for|against|conditional (map: for = evidence supports yes, against = evidence contradicts,
conditional = mixed or insufficient — use needs_research only if evidence_score < 0.20)
confidence and evidence_score: floats 0.0-1.0
evidence_for: list of factual claims WITH source URL in parentheses
evidence_against: list of factual claims WITH source URL in parentheses
evidence_gaps: list of what is NOT evidenced
recommendation: evidence report only — NOT strategy advice
influence_weight should be 0.4.
agent must be "researcher".
"""


async def run_researcher_agent(
    question: str,
    evidence: EvidencePacket,
    board_mode: BoardMode = "decision",
) -> dict[str, Any]:
    model = resolve_board_agent_model("researcher")
    user = f"""Question: {question}

## External research evidence packet
{evidence.text[:14000]}
"""
    raw = await complete_json(RESEARCHER_SYSTEM, user, model=model)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    data.setdefault("agent", "researcher")
    data.setdefault("question_answered", question)
    data["confidence"] = _as_float(data.get("confidence"), 0.5)
    data["influence_weight"] = _as_float(data.get("influence_weight"), 0.4)
    data.setdefault("evidence_quality", "moderate")
    data["research_age_days"] = 0
    data["evidence_score"] = _as_float(data.get("evidence_score"), 0.4 if evidence.source_count else 0.1)
    data["evidence_for"] = _as_str_list(data.get("evidence_for", []))
    data["evidence_against"] = _as_str_list(data.get("evidence_against", []))
    data["evidence_gaps"] = _as_str_list(data.get("evidence_gaps", []))
    data.setdefault("evidence_used", [])
    if not isinstance(data.get("evidence_used"), list):
        data["evidence_used"] = [
            {"source": item.url, "snippet": item.summary or item.snippet, "url": item.url}
            for item in evidence.items[:6]
        ]
    data["key_assumptions"] = _as_str_list(data.get("key_assumptions", []))
    data["risks"] = _as_str_list(data.get("risks", []))
    data["unknowns"] = _as_str_list(data.get("unknowns", [])) or data["evidence_gaps"]

    if not data.get("recommendation"):
        for_part = "; ".join(data["evidence_for"][:3]) or "None cited"
        against_part = "; ".join(data["evidence_against"][:3]) or "None cited"
        gaps_part = "; ".join(data["evidence_gaps"][:3]) or "None listed"
        data["recommendation"] = (
            f"Evidence for: {for_part}. Evidence against: {against_part}. Gaps: {gaps_part}."
        )

    data.setdefault("primary_pick", "evidence report")
    data.setdefault("suggested_next_action", "Close top evidence gap with one targeted source")
    data.setdefault("verdict", "conditional" if board_mode == "decision" else "needs_research")

    return enforce_agent_output(data, board_mode)
