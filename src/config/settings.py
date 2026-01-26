"""Application settings using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    llm_temperature: float = Field(default=0.7, ge=0, le=2)

    # GMX Email Configuration
    gmx_email: str = Field(default="alois_wirth@gmx.de")
    gmx_pw: str = Field(default="", description="GMX IMAP password")
    gmx_imap_server: str = Field(default="imap.gmx.net")
    gmx_imap_port: int = Field(default=993)
    gmx_smtp_server: str = Field(default="mail.gmx.net")
    gmx_smtp_port: int = Field(default=587)

    # GMX Calendar Configuration
    gmx_caldav_url: str = Field(default="")
    gmx_kalender: str = Field(default="", description="GMX CalDAV app password")

    # Storage Configuration
    storage_backend: Literal["local", "nas", "s3"] = Field(
        default="local", description="Storage backend to use"
    )
    storage_local_path: str = Field(default="./data")
    storage_nas_path: str = Field(default="")
    storage_s3_bucket: str = Field(default="")
    storage_s3_region: str = Field(default="eu-central-1")

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./data/personal_agent.db",
        description="Database connection URL",
    )

    # Application Settings
    timezone: str = Field(default="Europe/Berlin")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    @property
    def gmx_caldav_full_url(self) -> str:
        """Construct full CalDAV URL if not provided."""
        if self.gmx_caldav_url:
            return self.gmx_caldav_url
        return f"https://caldav.gmx.net/begenda/dav/{self.gmx_email}/calendar/"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
