# LiteLLM Proxy

A proxy to verify App Attest/FxA payloads and proxy requests through LiteLLM to enact budgets and per user management.

## Setup

```bash
make setup
```

This creates a virtual environment in `.venv/`, installs dependencies, and installs the tool locally in editable mode.

### Running LiteLLM Proxy locally with Docker
```bash
docker run --platform linux/amd64 --name litellm -v $(pwd)/litellm_config.yaml:/app/config.yaml -v $(pwd)/service_account.json:/app/service_account.json -p 4000:4000 ghcr.io/berriai/litellm:main-latest --config /app/config.yaml
```

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

### Example `litellm_config.yaml`
```yaml
model_list:
  - model_name: <provider>/<model_name>
    litellm_params:
      model: <provider>/<model_name>
      vertex_project: <gcp_project_name>
      vertex_location: <gcp_region>
      vertex_credentials: "/app/service_account.json"

general_settings:
  master_key: "sk-1234..." # match MASTER_KEY in .env
  database_url: "postgresql://user:password@host.docker.internal:5432/test"
  litellm_key_header_name: X-Litellm-Key
```

Service account configured to hit VertexAI: `service_account.json` should be in directory root

## API Documentation 

After running, Swagger can be viewed at `http://0.0.0.0:<PORT>/api/docs`
