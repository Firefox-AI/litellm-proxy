
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from contextlib import asynccontextmanager
from typing import Annotated, Optional
from .core.classes import UserUpdatePayload, AssertionRequestV2
from .core.routers.fxa import fxa_auth, fxa_router
from .core.routers.health import health_router
from .core.routers.appattest import appattest_router, app_attest_auth
from .core.config import settings
from .core.pg_services.services import key_pg, litellm_pg
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
    request_body: AssertionRequestV2,
    authorization: Annotated[str | None, Header()] = None
):
	if request_body and request_body.key_id and request_body.challenge and request_body.assertion_obj and request_body.payload:
		data = app_attest_auth(request_body)
		if data:
			if data.get("error"):
				raise HTTPException(status_code=400, detail=data["error"])
			return {"user_id": request_body.key_id, "payload": request_body.payload}
	if authorization:
		fxa_user_id = fxa_auth(authorization)
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
	await key_pg.connect()
	yield
	await litellm_pg.disconnect()
	await key_pg.disconnect()

app = FastAPI(
	title="LiteLLM Proxy",
	description="A proxy to verify App Attest/FxA payloads and proxy requests through LiteLLM.",
	version="1.0.0",
	docs_url="/api/docs",
	openapi_tags=tags_metadata,
	lifespan=lifespan
)

app.include_router(health_router, prefix="/health")
app.include_router(appattest_router, prefix="/verify")
app.include_router(fxa_router, prefix="/fxa")

@app.post("/v1/chat/completions", tags=["LiteLLM"], description="Authorize first using App Attest or FxA. Either pass the FxA token in the Authorization header or include the `{key_id, challenge, and assertion_obj}` in the request body. `payload` is always required and contains the prompt.", )
async def proxy_request(
	auth_res: Annotated[Optional[dict], Depends(authorize)],
):
	user_id = auth_res["user_id"]
	user, _ = await get_or_create_end_user(user_id)
	if (user.get("blocked")):
		raise HTTPException(
			status_code=403,
			detail={"error": "User is blocked."}
		)
	res = await completion(auth_res["payload"].text, user["user_id"])
	return res

@app.post("/user/update")
async def update_user_helper(
	request: UserUpdatePayload,
	master_key: str = Header(...)
):
	return await litellm_pg.update_user(request, master_key)

def main():
	uvicorn.run(app, host="0.0.0.0", port=settings.PORT, timeout_keep_alive=10)

if __name__ == "__main__":
	main()
