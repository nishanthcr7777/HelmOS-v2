from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: str = ""
    tavily_api_key: str = ""
    firecrawl_api_key: str = ""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    helmos_api_key: str = "dev-key"
    cors_origins: str = "http://localhost:3000"
    render_external_url: str = "http://localhost:8000"

    daily_spend_cap_usd: float = 5.0
    research_max_pages_per_session: int = 5
    embedding_model: str = "openai/text-embedding-3-small"
    chat_model: str = "openai/gpt-4o-mini"

    # Board agent models — JSON map e.g. {"researcher":"anthropic/claude-sonnet-4"}
    board_agent_models: str = ""
    board_agent_model_researcher: str = ""
    board_agent_model_skeptic: str = ""
    board_agent_model_operator: str = ""
    board_agent_model_sales: str = ""
    board_agent_model_cto: str = ""
    board_agent_model_synthesizer: str = ""

    storage_bucket: str = "helmos-files"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def get_settings() -> Settings:
    return Settings()
