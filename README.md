# Mozilla LLM Proxy Auth (MLPA)

A proxy to verify App Attest/FxA payloads and proxy requests through LiteLLM to enact budgets and per user management.

## Setup

```bash
make setup
```

This creates a virtual environment in `.venv/`, installs dependencies, and installs the tool locally in editable mode.

## Running MLPA locally with Docker

### Run LiteLLM
`docker compose -f litellm_docker_compose.yaml up -d`

### Run MLPA
`litellm-proxy`

## Config (see [LiteLLM Documentation](https://docs.litellm.ai/docs/simple_proxy_old_doc) for more config options)
`.env` (see `config.py` for all configuration variables)
```
MASTER_KEY="sk-1234..."
LITELLM_API_BASE="http://litellm.proxy:4000"
DATABASE_URL=postgresql://... # required for direct user editing in SQL
CHALLENGE_EXPIRY_SECONDS=300
PORT=8080

APP_BUNDLE_ID="org.example.app"
APP_DEVELOPMENT_TEAM="12BC943KDC"

CLIENT_ID="..."
CLIENT_SECRET="..."

SYSTEM_PROMPT="You are a helpful assistant..."
MODEL_NAME=""
TEMPERATURE=0.1
TOP_P=0.01
```

### Also See `litellm_config.yaml` for litellm config

Service account configured to hit VertexAI: `service_account.json` should be in directory root

## API Documentation 

After running, Swagger can be viewed at `http://localhost:<PORT>/api/docs`
