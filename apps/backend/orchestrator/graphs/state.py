"""Typed state for LangGraph board and research workflows."""

from typing import Any, TypedDict

from research.board_evidence import EvidencePacket


class ResearchState(TypedDict, total=False):
    question: str
    workspace_id: str
    workspace_context: str
    packet: EvidencePacket
    all_results: list[dict]
    relevant_raw: list[dict]
    research_trace: dict[str, Any]


class BoardState(TypedDict, total=False):
    question: str
    workspace_id: str
    project_id: str | None
    board_mode: str

    beliefs_list: list[Any]
    beliefs_block: str
    memory_result: Any
    board_ctx_text: str
    board_ctx_trace: dict[str, Any]

    evidence_packet: EvidencePacket
    research_trace: dict[str, Any]

    board_id: str
    agent_outputs: list[dict[str, Any]]
    researcher_debug: dict[str, Any]
    synthesis: dict[str, Any]
    decision_id: str
    board_session: Any
