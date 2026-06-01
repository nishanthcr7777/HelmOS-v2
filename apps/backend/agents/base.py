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
    data.setdefault("confidence", 0.5)
    data.setdefault("influence_weight", DEFAULT_WEIGHTS[agent_key])
    data.setdefault("evidence_quality", "moderate")
    data.setdefault("research_age_days", 7)
    data.setdefault("evidence_score", 0.5)
    data.setdefault("evidence_used", [])
    data.setdefault("key_assumptions", [])
    data.setdefault("risks", [])
    data.setdefault("unknowns", [])
    data.setdefault("recommendation", "Insufficient data — gather more evidence.")
    data.setdefault("suggested_next_action", "Run targeted research")
    return data
