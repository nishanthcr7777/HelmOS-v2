"""Board modes: exploration (open) vs decision (founder must get a pick)."""

from typing import Any, Literal

BoardMode = Literal["exploration", "decision"]

NEEDS_RESEARCH_MAX_EVIDENCE = 0.2

_EXPLORATION_VERDICTS = {
    "go",
    "no_go",
    "conditional",
    "lean_for",
    "lean_against",
    "needs_research",
    "for",
    "against",
}

_DECISION_TO_STORED = {
    "for": "lean_for",
    "go": "lean_for",
    "lean_for": "lean_for",
    "against": "lean_against",
    "no_go": "lean_against",
    "lean_against": "lean_against",
    "conditional": "conditional",
}


def _normalize_verdict_token(verdict: object) -> str:
    if not isinstance(verdict, str):
        return ""
    return verdict.strip().lower().replace(" ", "_").replace("-", "_")


def enforce_agent_output(data: dict[str, Any], board_mode: BoardMode) -> dict[str, Any]:
    evidence_score = float(data.get("evidence_score") or 0)
    verdict_raw = _normalize_verdict_token(data.get("verdict"))

    if board_mode == "decision":
        if verdict_raw == "needs_research":
            if evidence_score < NEEDS_RESEARCH_MAX_EVIDENCE:
                data["verdict"] = "needs_research"
            else:
                data["verdict"] = "conditional"
        elif verdict_raw in _DECISION_TO_STORED:
            data["verdict"] = _DECISION_TO_STORED[verdict_raw]
        else:
            data["verdict"] = "conditional"

        rec = str(data.get("recommendation") or "").strip()
        if not rec or rec.lower().startswith("insufficient"):
            pick = str(data.get("primary_pick") or "conditional pursuit").strip()
            conf = float(data.get("confidence") or 0.5)
            data["recommendation"] = (
                f"{pick}. Confidence {int(round(conf * 100))}%. "
                "Proceed with validation steps while acting on this lean."
            )
    else:
        if verdict_raw in _EXPLORATION_VERDICTS:
            mapped = _DECISION_TO_STORED.get(verdict_raw, verdict_raw)
            data["verdict"] = mapped if mapped in _EXPLORATION_VERDICTS else verdict_raw
        else:
            data["verdict"] = "needs_research"

    return data


def enforce_synthesis(
    data: dict[str, Any],
    question: str,
    board_mode: BoardMode,
) -> dict[str, Any]:
    from agents.base import _as_float

    confidence = _as_float(data.get("confidence"), 0.55)
    evidence_score = _as_float(data.get("evidence_score"), 0.4)
    verdict_raw = _normalize_verdict_token(data.get("verdict"))

    if board_mode == "decision":
        if verdict_raw == "needs_research" and evidence_score >= NEEDS_RESEARCH_MAX_EVIDENCE:
            data["verdict"] = "conditional"
        elif verdict_raw in _DECISION_TO_STORED:
            data["verdict"] = _DECISION_TO_STORED[verdict_raw]
        else:
            data["verdict"] = "conditional"
    else:
        if verdict_raw in _EXPLORATION_VERDICTS:
            data["verdict"] = _DECISION_TO_STORED.get(verdict_raw, verdict_raw)
        else:
            data["verdict"] = "conditional"

    direct = str(data.get("direct_answer") or "").strip()
    body = str(data.get("recommendation") or data.get("rationale") or "").strip()
    conf_pct = int(round(confidence * 100))

    if board_mode == "decision":
        if not direct:
            direct = _first_sentence(body) or "Conditional recommendation pending founder review"
        if not direct.endswith("."):
            direct += "."
        if body.lower().startswith(direct.lower().rstrip(".")):
            rest = body[len(direct.rstrip(".")) :].lstrip(". ").strip()
        else:
            rest = body
        data["recommendation"] = f"{direct} Confidence {conf_pct}%. {rest}".strip()
    else:
        data["recommendation"] = body or "Board could not reach consensus — defer decision."

    data["confidence"] = confidence
    data["evidence_score"] = evidence_score
    data["board_mode"] = board_mode
    return data


def _first_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    for sep in (". ", ".\n", "\n"):
        if sep in text:
            return text.split(sep, 1)[0].strip()
    return text[:240].strip()
