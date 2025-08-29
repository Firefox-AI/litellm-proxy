from pydantic_settings import BaseSettings
import yaml

class Settings(BaseSettings):
    debug: bool = False

    APPLE_PUBLIC_KEYS_URL: str
    CHALLENGE_EXPIRY_SECONDS: int
    JWT_SECRET: str
    JWT_EXPIRY_SECONDS: int

    MASTER_KEY: str # ex: sk-1234...
    LITELLM_API_BASE: str
    DATABASE_URL: str # postgres DB url
    PORT: int | None = 8080

    APP_BUNDLE_ID: str # ex: org.example.app
    APP_DEVELOPMENT_TEAM: str # ex: 12BC943KDC

    class Config:
        env_file = ".env"

settings = Settings()

LLM_CONFIG_PATH = "llm_config.yaml"
def load_llm_config(path=LLM_CONFIG_PATH):
    with open(path, "r") as f:
        return yaml.safe_load(f)

llm_config = load_llm_config()["llm_config"]