from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DEBUG: bool = False
    METRICS_LOG_FILE: str="metrics.jsonl"

    # LiteLLM
    MASTER_KEY: str # ex: sk-1234...
    LITELLM_API_BASE: str
    DATABASE_URL: str # postgres DB url
    CHALLENGE_EXPIRY_SECONDS: int = 300 # 5 minutes
    PORT: int | None = 8080
    
    # App Attest
    APP_BUNDLE_ID: str # ex: org.example.app
    APP_DEVELOPMENT_TEAM: str # ex: 12BC943KDC

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