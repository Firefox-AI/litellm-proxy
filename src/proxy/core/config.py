from pydantic_settings import BaseSettings


class Env(BaseSettings):
	DEBUG: bool = False
	METRICS_LOG_FILE: str = "metrics.jsonl"

	# PostgreSQL url (no /database)
	PG_DB_URL: str = "postgresql://user:password@localhost:5432"

	# LiteLLM
	MASTER_KEY: str = "sk-default"
	LITELLM_API_BASE: str = "http://localhost:8000"
	LITELLM_DB_NAME: str = "litellm"
	CHALLENGE_EXPIRY_SECONDS: int = 300  # 5 minutes
	PORT: int | None = 8080
	OPENAI_API_KEY: str | None = None

	# App Attest
	APP_BUNDLE_ID: str = "org.example.app"
	APP_DEVELOPMENT_TEAM: str = "TEAMID1234"
	APP_ATTEST_DB_NAME: str = "keys"

	# FxA
	CLIENT_ID: str = "default-client-id"
	CLIENT_SECRET: str = "default-client-secret"

	# LLM request default values
	MODEL_NAME: str = "gpt-4"
	TEMPERATURE: float = 0.1
	MAX_COMPLETION_TOKENS: int = 1024
	TOP_P: float = 0.01

	class Config:
		env_file = ".env"


env = Env()

LITELLM_READINESS_URL = f"{env.LITELLM_API_BASE}/health/readiness"
LITELLM_COMPLETIONS_URL = f"{env.LITELLM_API_BASE}/v1/chat/completions"
LITELLM_HEADERS = {
	"Content-Type": "application/json",
	"X-LiteLLM-Key": f"Bearer {env.MASTER_KEY}",
}
