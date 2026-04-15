"""
SUNDAY configuration — single source of truth.

All settings are loaded from environment variables / .env file.
Pydantic validates everything at startup so we fail fast on misconfig.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    model_config = SettingsConfigDict(env_prefix="SUNDAY_LLM_")

    primary_provider: Literal["groq", "google", "ollama"] = "groq"
    primary_model: str = "llama-3.3-70b-versatile"
    fallback_provider: Literal["groq", "google", "ollama"] = "google"
    fallback_model: str = "gemini-2.0-flash"
    offline_model: str = "qwen2.5:3b"

    # Rate limiting awareness
    max_retries: int = 2
    request_timeout: int = 30


class VoiceSettings(BaseSettings):
    """Voice pipeline configuration."""

    model_config = SettingsConfigDict(env_prefix="SUNDAY_")

    tts_voice: str = "en_US-amy-medium"
    stt_model: str = "base.en"
    vad_threshold: float = 0.5
    silence_duration_ms: int = 700  # ms of silence before we consider speech done
    sample_rate: int = 16000


class Settings(BaseSettings):
    """Root application settings."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        env_prefix="SUNDAY_",
        extra="ignore",
    )

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    debug: bool = False

    # Paths
    db_path: str = str(PROJECT_ROOT / "data" / "sunday.db")
    chroma_path: str = str(PROJECT_ROOT / "data" / "chroma")
    log_dir: str = str(PROJECT_ROOT / "data" / "logs")

    # API Keys (loaded from env)
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")

    # Sub-configs
    llm: LLMSettings = Field(default_factory=LLMSettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)

    # User context (single user for now, multi-user ready)
    default_user_id: str = "sunday-user"


# Singleton — import this everywhere
settings = Settings()
