"""
Application Configuration

All configuration is local-first with secure defaults.
No external service dependencies for core functionality.
"""

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with security-first defaults.
    
    Environment variables override these settings.
    Secrets should be provided via environment or secure key storage.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = "Insurabridge"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    
    # Paths (all local)
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".insurabridge" / "data")
    logs_dir: Path = Field(default_factory=lambda: Path.home() / ".insurabridge" / "logs")
    temp_dir: Path = Field(default_factory=lambda: Path.home() / ".insurabridge" / "temp")
    
    # Database (SQLite with encryption)
    db_path: Path = Field(default_factory=lambda: Path.home() / ".insurabridge" / "data" / "sentinel.db")
    db_encryption_key: SecretStr = Field(default=SecretStr("CHANGE_ME_IN_PRODUCTION"))
    
    # Vector Store (ChromaDB - local)
    chroma_path: Path = Field(default_factory=lambda: Path.home() / ".insurabridge" / "data" / "chroma")
    
    # LLM Configuration (Ollama - local only)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"  # Default model. Can also use gemma:2b, gemma:4b, or gemma:7b
    llm_temperature: float = 0.1  # Near-deterministic for consistency
    llm_max_tokens: int = 4096
    llm_timeout: int = 120  # seconds
    
    # Security
    secret_key: SecretStr = Field(default=SecretStr("CHANGE_ME_IN_PRODUCTION_USE_32_BYTES"))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # Short for security
    refresh_token_expire_days: int = 7
    password_min_length: int = 12
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    
    # Session
    session_timeout_minutes: int = 15
    
    # Audit
    audit_log_path: Path = Field(default_factory=lambda: Path.home() / ".insurabridge" / "logs" / "audit.log")
    audit_retention_days: int = 2555  # 7 years for HIPAA
    
    # OCR (Tesseract - local)
    tesseract_path: str | None = None  # Auto-detect if None
    
    # FHIR
    fhir_version: str = "R4"
    epic_sandbox_url: str = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
    
    # Rate Limiting (internal)
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    def validate_production_secrets(self) -> list[str]:
        """Check that production has proper secrets configured."""
        issues = []
        if self.is_production:
            if self.db_encryption_key.get_secret_value() == "CHANGE_ME_IN_PRODUCTION":
                issues.append("db_encryption_key must be changed for production")
            if self.secret_key.get_secret_value() == "CHANGE_ME_IN_PRODUCTION_USE_32_BYTES":
                issues.append("secret_key must be changed for production")
            if len(self.secret_key.get_secret_value()) < 32:
                issues.append("secret_key must be at least 32 bytes")
        return issues


# Global settings instance
settings = Settings()


# Validate on import in production
if settings.is_production:
    issues = settings.validate_production_secrets()
    if issues:
        raise ValueError(f"Production configuration errors: {', '.join(issues)}")

