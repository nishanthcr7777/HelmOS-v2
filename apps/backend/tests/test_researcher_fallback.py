from agents.researcher import _build_fallback_recommendation
from research.board_evidence import EvidencePacket


def test_fallback_no_sources():
    ev = EvidencePacket(tavily_hits=0, retrieval_case="no_sources")
    msg = _build_fallback_recommendation(ev, [], [], [])
    assert msg == "No external sources found."


def test_fallback_no_relevant():
    ev = EvidencePacket(tavily_hits=8, relevant_hits=0, retrieval_case="no_relevant")
    msg = _build_fallback_recommendation(ev, [], [], [])
    assert "8 sources retrieved" in msg
    assert "0 judged relevant" in msg


def test_fallback_has_relevant_but_empty_lists():
    ev = EvidencePacket(
        tavily_hits=8,
        relevant_hits=3,
        passed_to_researcher=3,
        retrieval_case="has_relevant",
    )
    msg = _build_fallback_recommendation(ev, [], [], [])
    assert "8 sources retrieved" in msg
    assert "3 passed" in msg
