import time
from typing import Annotated
from fastapi import Header, APIRouter
from fxa.oauth import Client
from ...config import env
from ...prometheus_metrics import metrics

router = APIRouter()
fxa_url = "https://api-accounts.stage.mozaws.net/v1" if env.DEBUG else "https://oauth.accounts.firefox.com/v1"
client = Client(env.CLIENT_ID, env.CLIENT_SECRET, fxa_url)

def fxa_auth(x_fxa_authorization: Annotated[str | None, Header()]):
	start_time = time.time()
	token = x_fxa_authorization.removeprefix("Bearer ").split()[0]
	try:
		profile = client.verify_token(token, scope="profile")
		metrics.validate_fxa_latency.labels(result="success").observe(time.time() - start_time)
	except Exception as e:
		metrics.validate_fxa_latency.labels(result="error").observe(time.time() - start_time)
		return {"error": f"Invalid FxA auth: {e}"}
	return profile