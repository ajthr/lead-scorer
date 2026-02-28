import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global system settings and infrastructure configuration.
    Sensitive org-specific credentials should be fetched from the database,
    while system-wide infrastructure (Postgres, MinIO, Redis) is managed here.
    """
    # System & DB
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DOCKER_MODE: bool = False  # Set to True when running inside a container

    # Database
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "lead_scorer_db"

    @property
    def DATABASE_URL(self) -> str:
        host = "postgres" if self.DOCKER_MODE else self.POSTGRES_HOST
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Storage (MinIO)
    MINIO_HOST: str = "localhost"
    MINIO_PORT: int = 9000
    MINIO_ROOT_USER: str = "admin"
    MINIO_ROOT_PASSWORD: str = "password"
    RAW_DATA_BUCKET: str = "raw-data"

    @property
    def MINIO_ENDPOINT(self) -> str:
        host = "minio" if self.DOCKER_MODE else self.MINIO_HOST
        return f"{host}:{self.MINIO_PORT}"

    # ML Lifecycle
    MLFLOW_HOST: str = "localhost"
    MLFLOW_PORT: int = 5000

    @property
    def MLFLOW_TRACKING_URI(self) -> str:
        host = "mlflow" if self.DOCKER_MODE else self.MLFLOW_HOST
        return f"http://{host}:{self.MLFLOW_PORT}"

    # Task Queue
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def REDIS_URL(self) -> str:
        host = "redis" if self.DOCKER_MODE else self.REDIS_HOST
        return f"redis://{host}:{self.REDIS_PORT}/0"

    # LLM Services
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4-turbo-preview"

    # Salesforce Global App Config
    SF_CLIENT_ID: Optional[str] = None
    SF_CLIENT_SECRET: Optional[str] = None
    SF_REDIRECT_URI: str = "http://localhost:8000/v1/auth/callback"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached instance of the system settings."""
    return Settings()

def get_org_context(org_id: str):
    """
    Enforces org-level isolation by returning settings or connection
    parameters specific to the requested org_id.
    
    This acts as a guardrail for data leakage prevention.
    """
    if not org_id:
        raise ValueError("org_id is required for isolation enforcement.")
    
    # In Phase 2, this will fetch org-specific Salesforce credentials 
    # and storage paths from the database.
    return {
        "org_id": org_id,
        "storage_prefix": f"orgs/{org_id}/",
        "log_prefix": f"ALS[{org_id}]"
    }
