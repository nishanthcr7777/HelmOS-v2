import json
from typing import Any

from llm.openrouter import complete_json


async def synthesize_board(question: str, agent_outputs: list[dict[str, Any]], beliefs_block: str) -> dict[str, Any]:
    system = f"""You synthesize a founder board session into one recommendation.
Return JSON with: recommendation, verdict, confidence, evidence_score, unknowns_level,
risks, unknowns, assumptions, next_action, rationale.

verdict: go|no_go|conditional|lean_for|lean_against|needs_research
unknowns_level: high|moderate|low

{beliefs_block}
"""
    user = json.dumps({"question": question, "agent_outputs": agent_outputs}, indent=2)[:14000]
    raw = await complete_json(system, user)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
    data.setdefault("recommendation", "Board could not reach consensus — defer decision.")
    data.setdefault("verdict", "conditional")
    data.setdefault("confidence", 0.5)
    data.setdefault("evidence_score", 0.5)
    data.setdefault("unknowns_level", "moderate")
    data.setdefault("risks", [])
    data.setdefault("unknowns", [])
    data.setdefault("assumptions", [])
    data.setdefault("next_action", "Review agent outputs and run research")
    return data
