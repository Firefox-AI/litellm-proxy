
import time
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from typing import Annotated, Optional
from .core.classes import AssertionRequest
from .core.config import env
from .core.pg_services.services import app_attest_pg, litellm_pg
from .core.prometheus_metrics import metrics
from .core.routers.appattest import appattest_router, app_attest_auth
from .core.routers.fxa import fxa_auth, fxa_router
from .core.routers.health import health_router
from .core.routers.user import user_router
from .core.utils import completion, get_or_create_end_user

tags_metadata = [
	{
		"name": "Health",
		"description": "Health check endpoints."
	},
	{
		"name": "App Attest",
		"description": "Endpoints for verifying App Attest payloads."
	}, 
	{
		"name": "FxA",
		"description": "Endpoints for verifying FxA tokens."
	},
	{
		"name": "LiteLLM",
		"description": "Endpoints for interacting with LiteLLM."
	}
]

async def authorize(
    request_body: AssertionRequest,
    x_fxa_authorization: Annotated[str | None, Header()] = None
):
	if request_body and request_body.key_id and request_body.challenge_b64 and request_body.assertion_obj_b64 and request_body.payload:
		data = await app_attest_auth(request_body)
		if data:
			if data.get("error"):
				raise HTTPException(status_code=400, detail=data["error"])
			return {"user": request_body.key_id, "payload": request_body.payload}
	if x_fxa_authorization:
		fxa_user_id = fxa_auth(x_fxa_authorization)
		if fxa_user_id:
			if fxa_user_id.get("error"):
				raise HTTPException(status_code=401, detail=fxa_user_id["error"])
			return {**fxa_user_id, "payload": request_body.payload}

	raise HTTPException(
		status_code=401,
		detail="Please authenticate with App Attest or FxA."
	)

@asynccontextmanager
async def lifespan(app: FastAPI):
	await litellm_pg.connect()
	await app_attest_pg.connect()
	yield
	await litellm_pg.disconnect()
	await app_attest_pg.disconnect()

app = FastAPI(
	title="LiteLLM Proxy",
	description="A proxy to verify App Attest/FxA payloads and proxy requests through LiteLLM.",
	version="1.0.0",
	docs_url="/api/docs",
	openapi_tags=tags_metadata,
	lifespan=lifespan
)

# run before all requests
@app.middleware("http")
async def instrument_requests(request: Request, call_next):
    """
    Measures request latency, counts total requests, and tracks requests in progress.
    """
    start_time = time.time()
    metrics.in_progress_requests.inc()

    try:
        response = await call_next(request)

        metrics.request_latency.observe(time.time() - start_time)

        route = request.scope.get('route')
        endpoint = route.path if route else request.url.path
        metrics.requests_total.labels(method=request.method, endpoint=endpoint).inc()
        metrics.response_status_codes.labels(status_code=response.status_code).inc()
        return response
    finally:
        metrics.in_progress_requests.dec()

@app.get("/metrics")
async def get_metrics():
	return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(health_router, prefix="/health")
app.include_router(appattest_router, prefix="/verify")
app.include_router(fxa_router, prefix="/fxa")
app.include_router(user_router, prefix="/user")

@app.post("/v1/chat/completions", tags=["LiteLLM"], description="Authorize first using App Attest or FxA. Either pass the FxA token in the Authorization header or include the `{key_id, challenge, and assertion_obj}` in the request body. `payload` is always required and contains the prompt.", )
async def chat_completion(
	auth_res: Annotated[Optional[dict], Depends(authorize)],
):
	user_id = auth_res["user"]
	user, _ = await get_or_create_end_user(user_id)
	if (user.get("blocked")):
		raise HTTPException(
			status_code=403,
			detail={"error": "User is blocked."}
		)
	res = await completion(auth_res["payload"]["text"], user["user_id"])
	return res

def main():
	uvicorn.run(app, host="0.0.0.0", port=env.PORT, timeout_keep_alive=10)

if __name__ == "__main__":
	main()
