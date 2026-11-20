from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Engine Execution Mode: 'mock' (offline) or 'live' (OpenAI / Grok)
    llm_mode: Literal["mock", "live"] = "mock"

    # Active LLM Provider
    llm_provider: Literal["openai", "grok"] = "openai"

    # OpenAI Settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Grok / xAI Settings
    xai_api_key: str = ""
    xai_model: str = "grok-beta"
    xai_base_url: str = "https://api.x.ai/v1"

    # Storage
    database_url: str = "sqlite:///./pulseops.db"
    db_path: Path = Path(__file__).resolve().parent.parent / "pulseops.db"

    # Guardrails & Timeouts
    max_tool_rounds: int = 6
    tool_timeout_seconds: float = 10.0

    # Paths
    project_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    docs_dir: Path = Path(__file__).resolve().parent.parent / "data" / "docs"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
