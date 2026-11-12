"""Application Settings.

Pydantic Settings model defining environment-based configuration parameters for Nammakam.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Nammakam services, feature flags, and integrations."""

    # Core Environment
    environment: str = Field(default="development", alias="NAMMAKAM_ENV")
    debug: bool = Field(default=False, alias="NAMMAKAM_DEBUG")

    # Cloud Infrastructure
    gcp_project_id: str = Field(default="nammakam-dev", alias="GCP_PROJECT_ID")
    gcp_region: str = Field(default="asia-south1", alias="GCP_REGION")

    # Feature Flags
    nammakam_enable_gemini_judge: bool = Field(
        default=False, alias="NAMMAKAM_ENABLE_GEMINI_JUDGE"
    )

    # Gemini Judge Configuration
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash-lite", alias="GEMINI_MODEL")
    gemini_prompt_version: str = Field(default="v1.0.0", alias="GEMINI_PROMPT_VERSION")
    gemini_max_retries: int = Field(default=3, alias="GEMINI_MAX_RETRIES")
    gemini_timeout_seconds: float = Field(default=30.0, alias="GEMINI_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# Singleton settings instance
settings = Settings()
