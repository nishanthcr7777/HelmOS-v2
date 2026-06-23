from unittest.mock import patch

from llm.agent_models import DEFAULT_BOARD_AGENT_MODELS, resolve_board_agent_model


def test_default_models_differ_by_role():
    assert DEFAULT_BOARD_AGENT_MODELS["researcher"] != DEFAULT_BOARD_AGENT_MODELS["operator"]
    assert DEFAULT_BOARD_AGENT_MODELS["synthesizer"] == DEFAULT_BOARD_AGENT_MODELS["researcher"]


def test_per_agent_env_override():
    with patch("llm.agent_models.get_settings") as mock_settings:
        mock_settings.return_value.board_agent_models = ""
        mock_settings.return_value.chat_model = "openai/gpt-4o-mini"
        mock_settings.return_value.board_agent_model_researcher = "custom/research-model"
        mock_settings.return_value.board_agent_model_skeptic = ""
        mock_settings.return_value.board_agent_model_operator = ""
        mock_settings.return_value.board_agent_model_sales = ""
        mock_settings.return_value.board_agent_model_cto = ""
        mock_settings.return_value.board_agent_model_synthesizer = ""
        assert resolve_board_agent_model("researcher") == "custom/research-model"


def test_json_map_override():
    with patch("llm.agent_models.get_settings") as mock_settings:
        mock_settings.return_value.board_agent_models = '{"cto": "openai/gpt-4o"}'
        mock_settings.return_value.chat_model = "openai/gpt-4o-mini"
        for f in (
            "board_agent_model_researcher",
            "board_agent_model_skeptic",
            "board_agent_model_operator",
            "board_agent_model_sales",
            "board_agent_model_cto",
            "board_agent_model_synthesizer",
        ):
            setattr(mock_settings.return_value, f, "")
        assert resolve_board_agent_model("cto") == "openai/gpt-4o"
