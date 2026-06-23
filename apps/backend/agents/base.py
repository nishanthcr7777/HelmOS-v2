import json
from typing import Any

from agents.board_modes import BoardMode, enforce_agent_output
from agents.prompts import AGENT_ROLE_BLOCKS
from llm.agent_models import resolve_board_agent_model
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
        n = float(value)  # type: ignore[arg-type]
        if n != n:  # NaN
            return default
        if n > 1.0 and n <= 100.0:
            return n / 100.0
        return max(0.0, min(1.0, n))
    except (TypeError, ValueError):
        return default


def _decision_mode_prompt() -> str:
    return """
BOARD MODE: DECISION — founder needs a usable pick, not abstention.

Rules (mandatory):
- verdict MUST be exactly one of: for | against | conditional
  Map mentally: for = lean yes, against = lean no, conditional = yes with caveats
- needs_research is FORBIDDEN unless evidence_score is below 0.20
- primary_pick: one concrete answer to the question (sector, target, option name, or "conditional: X")
- recommendation MUST start with primary_pick, then "Confidence NN%", then rationale
- If choosing between sectors/options (e.g. SaaS vs logistics), PICK ONE even if uncertain
- An imperfect recommendation beats refusing to choose

Founder principle: An imperfect recommendation is more useful than five abstentions.
"""


def _exploration_mode_prompt() -> str:
    return """
BOARD MODE: EXPLORATION — open analysis; needs_research is allowed when evidence is thin.
verdict: go|no_go|conditional|lean_for|lean_against|needs_research
"""


def build_system_prompt(
    agent_key: str,
    beliefs_block: str,
    board_mode: BoardMode = "decision",
) -> str:
    label = AGENT_LABELS[agent_key]
    role_block = AGENT_ROLE_BLOCKS[agent_key]
    mode_block = _decision_mode_prompt() if board_mode == "decision" else _exploration_mode_prompt()
    verdict_field = (
        "verdict: for|against|conditional (needs_research ONLY if evidence_score < 0.20)"
        if board_mode == "decision"
        else "verdict: go|no_go|conditional|lean_for|lean_against|needs_research"
    )
    return f"""You are the {label} on a founder intelligence board.

{role_block}

Respond in JSON only with keys:
agent, question_answered, verdict, confidence, influence_weight, evidence_quality,
research_age_days, evidence_score, evidence_used, key_assumptions, risks, unknowns,
primary_pick, recommendation, suggested_next_action.

{verdict_field}
confidence and evidence_score: floats 0.0-1.0 (NOT words like "low" or "high")
evidence_quality: high|moderate|low
influence_weight should be {DEFAULT_WEIGHTS[agent_key]}.
agent must be "{agent_key}".

{mode_block}

{beliefs_block}
"""


async def run_agent(
    agent_key: str,
    question: str,
    context: str,
    beliefs_block: str,
    board_mode: BoardMode = "decision",
    model: str | None = None,
) -> dict[str, Any]:
    if agent_key == "researcher":
        raise ValueError("Use run_researcher_agent() for the researcher role")

    system = build_system_prompt(agent_key, beliefs_block, board_mode)
    user = f"Question: {question}\n\nContext:\n{context[:12000]}"
    resolved_model = model or resolve_board_agent_model(agent_key)
    raw = await complete_json(system, user, model=resolved_model)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    data.setdefault("agent", agent_key)
    data.setdefault("question_answered", question)
    data["confidence"] = _as_float(data.get("confidence"), 0.55)
    data["influence_weight"] = _as_float(data.get("influence_weight"), DEFAULT_WEIGHTS[agent_key])
    data.setdefault("evidence_quality", "moderate")
    data["research_age_days"] = int(_as_float(data.get("research_age_days"), 7))
    data["evidence_score"] = _as_float(data.get("evidence_score"), 0.35)
    data.setdefault("evidence_used", [])
    data["key_assumptions"] = _as_str_list(data.get("key_assumptions", []))
    data["risks"] = _as_str_list(data.get("risks", []))
    data["unknowns"] = _as_str_list(data.get("unknowns", []))
    if not isinstance(data.get("evidence_used"), list):
        data["evidence_used"] = []
    data.setdefault("primary_pick", "")
    data.setdefault(
        "recommendation",
        "Conditional pursuit — validate with one targeted conversation this week.",
    )
    data.setdefault("suggested_next_action", "Run one validation step on the primary pick")

    if board_mode == "decision":
        data.setdefault("verdict", "conditional")
    else:
        data.setdefault("verdict", "needs_research")

    return enforce_agent_output(data, board_mode)
