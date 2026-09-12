from __future__ import annotations

import json
import os
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_comma_env(var_name: str, default: list[str]) -> list[str]:
    """Parse a comma-separated or JSON array env var into a list."""
    raw = os.environ.get(var_name, "")
    if not raw:
        return default
    raw = raw.strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    return [v.strip() for v in raw.split(",") if v.strip()]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "BlackSentinel Pulse"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://pulse:pulse@localhost:5432/blacksentinel_pulse"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "pulse"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS - parsed from comma-separated env var (ALLOWED_ORIGINS)
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    ALLOWED_HOSTS: list[str] = ["*"]

    # External APIs
    SHODAN_API_KEY: str = ""
    CENSYS_API_ID: str = ""
    CENSYS_API_SECRET: str = ""

    # Cloud Provider Keys
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""

    GCP_PROJECT_ID: str = ""
    GCP_CREDENTIALS_PATH: str = ""

    # Threat Intelligence
    VIRUSTOTAL_API_KEY: str = ""
    ABUSEIPDB_API_KEY: str = ""

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Discovery Engine
    DISCOVERY_SCAN_INTERVAL: int = 3600
    MAX_CONCURRENT_DISCOVERIES: int = 10
    ASSET_RETENTION_DAYS: int = 90

    # ML Engine
    ML_MODEL_PATH: str = "./ml_models"
    RISK_SCORE_WEIGHTS: dict[str, float] = {
        "vulnerability": 0.3,
        "exposure": 0.25,
        "criticality": 0.2,
        "threat_intel": 0.15,
        "age": 0.1,
    }


def get_settings() -> Settings:
    """Create Settings with comma-separated env var support."""
    # Pre-process list env vars before pydantic-settings sees them
    os.environ["ALLOWED_ORIGINS"] = json.dumps(
        _parse_comma_env("ALLOWED_ORIGINS", ["http://localhost:3000", "http://localhost:5173"])
    )
    os.environ["ALLOWED_HOSTS"] = json.dumps(
        _parse_comma_env("ALLOWED_HOSTS", ["*"])
    )
    return Settings()


settings = get_settings()
