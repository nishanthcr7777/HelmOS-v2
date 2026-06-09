from agents.base import AGENT_NAMES, build_system_prompt
from agents.prompts import AGENT_ROLE_BLOCKS


def test_every_agent_has_role_block():
    for key in AGENT_NAMES:
        assert key in AGENT_ROLE_BLOCKS
        assert AGENT_ROLE_BLOCKS[key].strip()


def test_skeptic_is_adversarial():
    block = AGENT_ROLE_BLOCKS["skeptic"]
    assert "prove the board wrong" in block
    assert "consensus is often mistaken" in block
    assert "leading recommendation fails" in block


def test_researcher_evidence_only():
    block = AGENT_ROLE_BLOCKS["researcher"]
    assert "only use evidence" in block.lower()
    assert "do not speculate" in block.lower()


def test_system_prompt_includes_role_block():
    prompt = build_system_prompt("skeptic", "## Strategic beliefs\n- test", "decision")
    assert "prove the board wrong" in prompt
    assert "Skeptic" in prompt


def test_agents_have_different_role_blocks():
    skeptic = build_system_prompt("skeptic", "", "decision")
    sales = build_system_prompt("sales_strategist", "", "decision")
    assert skeptic != sales
