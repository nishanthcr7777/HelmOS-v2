"""Resolve per-agent board model from settings."""

import json

from config import get_settings

# Defaults when BOARD_AGENT_MODELS env is unset — override via env, not in agent code.
DEFAULT_BOARD_AGENT_MODELS: dict[str, str] = {
    "researcher": "anthropic/claude-sonnet-4",
    "skeptic": "anthropic/claude-sonnet-4",
    "operator": "openai/gpt-4o-mini",
    "sales_strategist": "openai/gpt-4o-mini",
    "cto": "openai/gpt-4o-mini",
    "synthesizer": "anthropic/claude-sonnet-4",
}

_PER_AGENT_ENV_FIELDS = {
    "researcher": "board_agent_model_researcher",
    "skeptic": "board_agent_model_skeptic",
    "operator": "board_agent_model_operator",
    "sales_strategist": "board_agent_model_sales",
    "cto": "board_agent_model_cto",
    "synthesizer": "board_agent_model_synthesizer",
}


def resolve_board_agent_model(agent_key: str) -> str:
    settings = get_settings()
    models = dict(DEFAULT_BOARD_AGENT_MODELS)

    if settings.board_agent_models.strip():
        try:
            parsed = json.loads(settings.board_agent_models)
            if isinstance(parsed, dict):
                models.update({k: str(v) for k, v in parsed.items()})
        except json.JSONDecodeError:
            pass

    env_field = _PER_AGENT_ENV_FIELDS.get(agent_key)
    if env_field:
        override = getattr(settings, env_field, "") or ""
        if override.strip():
            return override.strip()

    return models.get(agent_key, settings.chat_model)
