# Guidelines for Contributions

## Local setup

### Dev requirements

We recommend to use [uv](https://docs.astral.sh/uv/getting-started/installation/):

1. `make`
2. `source .venv/bin/activate`

### Lint

Ensure all the checks pass:

`pre-commit run --all-files --verbose`

## Installation

`make install`

## Tests

Ensure all tests pass: `pytest -v`

## Local Build for QA and manuall testing

1. Use `litellm_docker_compose.yaml` to start LiteLLM and Postgress locally:

  ```bash
  docker compose -f litellm_docker_compose.yaml up -d
  ```

  or if you are using legacy docker-compose

  ```bash
  docker-compose -f litellm_docker_compose.yaml up -d
  ```

2. Create a second database that is needed for authentification

  ```
  bash scripts/create-app-attest-database.sh
  ```

LiteLLm will be accesible at `localhost:4000` and `localhost:4000/ui`

1. Run the MLPA with

  ```bash
  mlpa
  ```

2. Kill the service with

```
docker compose -f litellm_docker_compose.yaml down
```

### Useful CURLs for QA

1. MLPA liveness:

```bash
curl --location 'http://0.0.0.0:8080/health/liveness' \
--header 'Content-Type: application/json'
```

2. MLPA readiness:

```bash
curl --location 'http://0.0.0.0:8080/health/readiness' \
--header 'Content-Type: application/json'
```

3. MLPA completion:

  ```bash
  curl --location 'http://0.0.0.0:8080/v1/chat/completions' \
  --header 'Content-Type: application/json' \
  --header 'x-fxa-authorization: Bearer {YOUR_MOZILLA_FXA_TOKEN}' \
  --header 'X-LiteLLM-Key: Bearer {MASTER_KEY}' \
  --data '{
   "model": "openai/gpt-4o",
    "messages": [{
       "role": "user",
       "content": "Hello!"
     }]
  }'
  ```

4. LiteLLM liveness:

```bash
curl --location 'http://localhost:4000/health/liveness' \
--header 'Content-Type: application/json'
```

5. List of available models:

```bash
curl --location 'http://localhost:4000/models' \
--header 'Content-Type: application/json' \
--header 'X-Litellm-Key: Bearer {MASTER_KEY}' \
--data ''
```

6. Completion directly from LiteLLM:

```bash
curl --location 'http://localhost:4000/v1/chat/completions' \
--header 'Content-Type: application/json' \
--header 'X-LiteLLM-Key: Bearer {MASTER_KEY}' \
--data '{
    "model": "openai/gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": "what is 2+2?"
      }
    ]
}'
```


## FXA tokens and where to find them
MLPA is using [https://github.com/mozilla/PyFxA](https://github.com/mozilla/PyFxA) library for authentification with Mozilla account. Please follow quick start instructions in their [Readme](https://github.com/mozilla/PyFxA?tab=readme-ov-file#using-firefox-account-bearer-token-with-requests).

Here is a quick snippet:
```python

from fxa.tools.bearer import get_bearer_token

fxa_token: str = get_bearer_token(
    your_mozilla_account_email,
    your_mozilla_account_password,
    scopes=["profile"],
    client_id="5882386c6d801776" # a common client_id for dev environment,
    account_server_url="https://api.accounts.firefox.com",
    oauth_server_url="https://oauth.accounts.firefox.com",
)
```
