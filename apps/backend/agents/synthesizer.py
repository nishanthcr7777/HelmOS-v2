import json
from typing import Any

from agents.base import _as_float
from agents.board_modes import BoardMode, enforce_synthesis
from llm.openrouter import complete_json


async def synthesize_board(
    question: str,
    agent_outputs: list[dict[str, Any]],
    beliefs_block: str,
    board_mode: BoardMode = "decision",
) -> dict[str, Any]:
    mode_block = ""
    if board_mode == "decision":
        mode_block = """
DECISION MODE synthesis rules (mandatory):
- direct_answer: ONE sentence that answers the founder's question directly (pick an option/sector/target)
- recommendation: direct_answer first, then "Confidence NN%", then risks/unknowns analysis
- verdict: for|against|conditional only (map to lean_for/lean_against/conditional); needs_research ONLY if evidence_score < 0.20
- Never open with "need more research" or "insufficient data" unless evidence_score < 0.20
- Example: "SaaS." as direct_answer for a sector question — then full recommendation with confidence

Founder principle: An imperfect recommendation is more useful than five abstentions.
"""
    else:
        mode_block = """
EXPLORATION MODE: broader analysis allowed; needs_research verdict OK when appropriate.
"""

    system = f"""You synthesize a founder board session into one recommendation.
Return JSON with: direct_answer, recommendation, verdict, confidence, evidence_score, unknowns_level,
risks, unknowns, assumptions, next_action, rationale.

confidence and evidence_score: floats 0.0-1.0
unknowns_level: high|moderate|low

{mode_block}

{beliefs_block}
"""
    user = json.dumps({"question": question, "agent_outputs": agent_outputs}, indent=2)[:14000]
    raw = await complete_json(system, user)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    from agents.base import _as_str_list

    data.setdefault("direct_answer", "")
    data.setdefault("recommendation", "Board could not reach consensus — defer decision.")
    data.setdefault("verdict", "conditional")
    data["confidence"] = _as_float(data.get("confidence"), 0.55)
    data["evidence_score"] = _as_float(data.get("evidence_score"), 0.4)
    data.setdefault("unknowns_level", "moderate")
    data["risks"] = _as_str_list(data.get("risks", []))
    data["unknowns"] = _as_str_list(data.get("unknowns", []))
    data["assumptions"] = _as_str_list(data.get("assumptions", []))
    data.setdefault("next_action", "Validate the primary pick with one founder-led conversation")

    return enforce_synthesis(data, question, board_mode)
