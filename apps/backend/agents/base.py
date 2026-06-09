import json
from typing import Any

from llm.openrouter import complete_json

AGENT_NAMES = ["cto", "operator", "skeptic", "researcher", "sales_strategist"]

AGENT_LABELS = {
    "cto": "CTO",
    "operator": "Operator",
    "skeptic": "Skeptic",
    "researcher": "Researcher",
    "sales_strategist": "Sales Strategist",
}

DEFAULT_WEIGHTS = {
    "cto": 0.05,
    "operator": 0.2,
    "skeptic": 0.25,
    "researcher": 0.4,
    "sales_strategist": 0.1,
}


def _as_str_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _as_float(value: object, default: float = 0.5) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


async def run_agent(
    agent_key: str,
    question: str,
    context: str,
    beliefs_block: str,
) -> dict[str, Any]:
    label = AGENT_LABELS[agent_key]
    system = f"""You are the {label} on a founder intelligence board.
Respond in JSON only with keys:
agent, question_answered, verdict, confidence, influence_weight, evidence_quality,
research_age_days, evidence_score, evidence_used, key_assumptions, risks, unknowns,
recommendation, suggested_next_action.

verdict: go|no_go|conditional|lean_for|lean_against|needs_research
evidence_quality: high|moderate|low
influence_weight should be {DEFAULT_WEIGHTS[agent_key]}.
agent must be "{agent_key}".

{beliefs_block}
"""
    user = f"Question: {question}\n\nContext:\n{context[:12000]}"
    raw = await complete_json(system, user)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
    data.setdefault("agent", agent_key)
    data.setdefault("question_answered", question)
    data.setdefault("verdict", "needs_research")
    data["confidence"] = _as_float(data.get("confidence"), 0.5)
    data["influence_weight"] = _as_float(data.get("influence_weight"), DEFAULT_WEIGHTS[agent_key])
    data.setdefault("evidence_quality", "moderate")
    data["research_age_days"] = int(_as_float(data.get("research_age_days"), 7))
    data["evidence_score"] = _as_float(data.get("evidence_score"), 0.5)
    data.setdefault("evidence_used", [])
    data["key_assumptions"] = _as_str_list(data.get("key_assumptions", []))
    data["risks"] = _as_str_list(data.get("risks", []))
    data["unknowns"] = _as_str_list(data.get("unknowns", []))
    if not isinstance(data.get("evidence_used"), list):
        data["evidence_used"] = []
    data.setdefault("recommendation", "Insufficient data — gather more evidence.")
    data.setdefault("suggested_next_action", "Run targeted research")
    return data
