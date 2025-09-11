from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DEBUG: bool = False
    METRICS_LOG_FILE: str="metrics.jsonl"

    # PostgreSQL url (no /database)
    PG_DB_URL: str # postgres DB url, ex: postgresql://user:password@host:port

    # LiteLLM
    MASTER_KEY: str # ex: sk-1234...
    LITELLM_API_BASE: str
    LITELLM_DB_NAME: str # litellm database name ex: litellm
    CHALLENGE_EXPIRY_SECONDS: int = 300 # 5 minutes
    PORT: int | None = 8080
    
    # App Attest
    APP_BUNDLE_ID: str # ex: org.example.app
    APP_DEVELOPMENT_TEAM: str # ex: 12BC943KDC
    APP_ATTEST_DB_NAME: str # app attest public key database name: keys

    # FxA
    CLIENT_ID: str
    CLIENT_SECRET: str

    # LLM
    SYSTEM_PROMPT: str = "You are a helpful assistant."
    MODEL_NAME: str
    TEMPERATURE: float = 0.1
    TOP_P: float = 0.01

    class Config:
        env_file = ".env"

settings = Settings()