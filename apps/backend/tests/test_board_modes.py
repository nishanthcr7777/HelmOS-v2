from agents.board_modes import enforce_agent_output, enforce_synthesis


def test_decision_mode_blocks_needs_research_when_evidence_sufficient():
    out = enforce_agent_output(
        {"verdict": "needs_research", "evidence_score": 0.45, "confidence": 0.62},
        "decision",
    )
    assert out["verdict"] == "conditional"


def test_decision_mode_allows_needs_research_when_evidence_thin():
    out = enforce_agent_output(
        {"verdict": "needs_research", "evidence_score": 0.15, "confidence": 0.3},
        "decision",
    )
    assert out["verdict"] == "needs_research"


def test_decision_mode_maps_for_to_lean_for():
    out = enforce_agent_output({"verdict": "for", "evidence_score": 0.5}, "decision")
    assert out["verdict"] == "lean_for"


def test_synthesis_direct_answer_first_in_decision_mode():
    out = enforce_synthesis(
        {
            "direct_answer": "SaaS",
            "recommendation": "Risks include crowded market.",
            "verdict": "for",
            "confidence": 0.62,
            "evidence_score": 0.4,
        },
        "Should Clawback target SaaS, logistics, or manufacturing?",
        "decision",
    )
    assert out["recommendation"].startswith("SaaS. Confidence 62%.")
    assert out["verdict"] == "lean_for"
