"""
Application Configuration
Load from environment variables with secure defaults
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Application
    APP_NAME: str = "Claims Automation Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: SecretStr = Field(default=SecretStr("CHANGE_IN_PRODUCTION"))
    API_BASE_URL: str = "http://localhost:8000"
    
    # Database
    DATABASE_URL: str = "postgresql://claims_user:claims_password@localhost:5432/claims_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    
    # Security
    SESSION_SECRET: SecretStr = Field(default=SecretStr("CHANGE_IN_PRODUCTION"))
    SESSION_TIMEOUT_MINUTES: int = 15
    CORS_ORIGINS: str = "http://localhost:3000"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    
    # Epic EHR
    EPIC_CLIENT_ID: str = ""
    EPIC_CLIENT_SECRET: SecretStr = Field(default=SecretStr(""))
    EPIC_REDIRECT_URI: str = "http://localhost:8000/auth/epic/callback"
    EPIC_FHIR_BASE: str = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
    EPIC_AUTH_URL: str = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"
    EPIC_TOKEN_URL: str = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
    
    # Cerner EHR
    CERNER_CLIENT_ID: str = ""
    CERNER_CLIENT_SECRET: SecretStr = Field(default=SecretStr(""))
    CERNER_REDIRECT_URI: str = "http://localhost:8000/auth/cerner/callback"
    CERNER_FHIR_BASE: str = "https://fhir-myrecord.cerner.com/r4"
    CERNER_AUTH_URL: str = "https://authorization.cerner.com/oauth2/authorize"
    CERNER_TOKEN_URL: str = "https://authorization.cerner.com/oauth2/token"
    
    # eClinicalWorks
    ECLINICALWORKS_CLIENT_ID: str = ""
    ECLINICALWORKS_CLIENT_SECRET: SecretStr = Field(default=SecretStr(""))
    ECLINICALWORKS_REDIRECT_URI: str = "http://localhost:8000/auth/eclinicalworks/callback"
    ECLINICALWORKS_FHIR_BASE: str = "https://fhir.eclinicalworks.com/fhir/r4"
    ECLINICALWORKS_AUTH_URL: str = "https://oauth.eclinicalworks.com/authorize"
    ECLINICALWORKS_TOKEN_URL: str = "https://oauth.eclinicalworks.com/token"
    
    # Athenahealth
    ATHENAHEALTH_CLIENT_ID: str = ""
    ATHENAHEALTH_CLIENT_SECRET: SecretStr = Field(default=SecretStr(""))
    ATHENAHEALTH_REDIRECT_URI: str = "http://localhost:8000/auth/athenahealth/callback"
    ATHENAHEALTH_FHIR_BASE: str = "https://fhir.platform.athenahealth.com/fhir/r4"
    ATHENAHEALTH_AUTH_URL: str = "https://api.platform.athenahealth.com/oauth2/v1/authorize"
    ATHENAHEALTH_TOKEN_URL: str = "https://api.platform.athenahealth.com/oauth2/v1/token"
    
    # Meditech
    MEDITECH_CLIENT_ID: str = ""
    MEDITECH_CLIENT_SECRET: SecretStr = Field(default=SecretStr(""))
    MEDITECH_REDIRECT_URI: str = "http://localhost:8000/auth/meditech/callback"
    MEDITECH_FHIR_BASE: str = "https://fhir.meditech.com/api/fhir/r4"
    MEDITECH_AUTH_URL: str = "https://fhir.meditech.com/oauth/authorize"
    MEDITECH_TOKEN_URL: str = "https://fhir.meditech.com/oauth/token"
    
    # Local LLM Service
    LLM_SERVICE_URL: str = "http://localhost:8001"
    LLM_TIMEOUT_SECONDS: int = 120
    LLM_MAX_RETRIES: int = 3
    
    # Data Retention
    DATA_RETENTION_DAYS: int = 2555  # 7 years
    AUDIT_LOG_RETENTION_DAYS: int = 2555
    SESSION_RETENTION_DAYS: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SESSION_PREFIX: str = "session:"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Feature Flags
    ENABLE_MOCK_EHR: bool = False
    ENABLE_AUDIT_LOGGING: bool = True
    ENABLE_ANALYTICS: bool = False
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"
    
    def validate_production_config(self) -> list[str]:
        """Validate production configuration."""
        issues = []
        if self.is_production:
            if self.SECRET_KEY.get_secret_value() == "CHANGE_IN_PRODUCTION":
                issues.append("SECRET_KEY must be changed for production")
            if self.SESSION_SECRET.get_secret_value() == "CHANGE_IN_PRODUCTION":
                issues.append("SESSION_SECRET must be changed for production")
            if not self.EPIC_CLIENT_ID and not self.ENABLE_MOCK_EHR:
                issues.append("At least one EHR provider must be configured")
        return issues


# Global settings instance
settings = Settings()

# Validate on import in production
if settings.is_production:
    issues = settings.validate_production_config()
    if issues:
        raise ValueError(f"Production configuration errors: {', '.join(issues)}")
