
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
import httpx
from typing import Annotated
import asyncpg
from .core.classes import MessagesPayload, UserUpdatePayload, Timer
from .core.fxa import get_fxa_user_id
from .core.appattest import get_current_session, appattest_router
from .core.appattest.config import settings

LITELLM_VIRTUAL_KEY_URL = f"{settings.LITELLM_API_BASE}/key/generate"
LITELLM_COMPLETIONS_URL = f"{settings.LITELLM_API_BASE}/v1/chat/completions"
LITELLM_HEADERS = {
	"Content-Type": "application/json",
	"X-LiteLLM-Key": f"Bearer {settings.MASTER_KEY}"
}
METRICS_LOG_FILE = "metrics.jsonl"


def get_optional_app_attest_session(proxy_auth: str = Header(...)):
	try:
		session = get_current_session(proxy_auth)
		return session
	except HTTPException:
		return None


def get_optional_fxa_user_id(proxy_auth: str = Header(...)):
	try:
		user_id = get_fxa_user_id(proxy_auth)
		return user_id
	except HTTPException:
		return None


async def get_user_id_from_either(
	app_attest_session: Annotated[dict, Depends(get_optional_app_attest_session)],
	fxa_user_id: Annotated[str, Depends(get_optional_fxa_user_id)]
):
	timer = Timer()
	timer.start()
	if app_attest_session:
		timer.checkpoint("app_attest_verification")
		return [app_attest_session["user_id"], timer]
	if fxa_user_id:
		timer.checkpoint("fxa_user_verification")
		return [fxa_user_id, timer]
	raise HTTPException(
		status_code=401,
		detail={"error": "Not authenticated with App Attest or FxA."}
	)

app = FastAPI(
	title="LiteLLM Proxy",
	description="A proxy to verify App Attest/FxA payloads and proxy requests through LiteLLM.",
	version="1.0.0"
)
# Setup
# - GET /verify/challenge?device_id=...
# - POST /verify/attest
# - POST /verify/attest_v2
app.include_router(appattest_router, prefix="/verify")

async def completion(messages, end_user_id: str):
	body = {"model": "vertex_ai/mistral-small-2503", "messages": messages, "user": end_user_id}
	try:
		async with httpx.AsyncClient() as client:
			response = await client.post(LITELLM_COMPLETIONS_URL, headers=LITELLM_HEADERS, json=body, timeout=10)
			data = response.json()
			return data
	except Exception as e:
		raise HTTPException(
			status_code=500,
			detail={"error": f"Failed to proxy request to {LITELLM_COMPLETIONS_URL}: {e}"}
		)

@app.post("/v1/chat/completions")
async def proxy_request(
	chat_request: MessagesPayload,
	auth_res=Depends(get_user_id_from_either)
):
	user_id, timer = auth_res
	user, created = await get_or_create_end_user(user_id)
	if (user.get("blocked")):
		raise HTTPException(
			status_code=403,
			detail={"error": "User is blocked."}
		)
	timer.checkpoint("create_user" if created else "get_user")
	res = await completion(chat_request.messages, user["user_id"])
	if res.get("error"):
		timer.checkpoint(res["error"].get("type", "completion_error"))
	else:
		timer.checkpoint("completion")
	timer.log()
	return res

@app.post("/user/update")
async def update_user(
	request: UserUpdatePayload,
	master_key: str = Header(...)
):
	"""
	Allow updating the user's (End User/Customer)'s information
	Free tier of LiteLLM does not support this, so updating the DB directly
	is a workaround.
	example POST body: {
		"user_id": "test-user-32",
		"blocked": false,
		"budget_id": null,
		"alias": null
	}
	"""
	if master_key != f"Bearer {settings.MASTER_KEY}":
		raise HTTPException(status_code=401, detail={"error": "Unauthorized"})

	if not settings.DATABASE_URL:
		raise ValueError("DATABASE_URL environment variable not set.")

	update_data = request.model_dump(exclude_unset=True)
	user_id = update_data.pop("user_id", request.user_id) 

	if not update_data:
		return {"status": "no fields to update", "user_id": user_id}

	conn = await asyncpg.connect(settings.DATABASE_URL)
	updated_user_record = None
	try:
		set_clause = ", ".join([f'"{key}" = ${i+1}' for i, key in enumerate(update_data.keys())])
		values = list(update_data.values())
		where_value_index = len(values) + 1
		
		query = f'UPDATE "LiteLLM_EndUserTable" SET {set_clause} WHERE user_id = ${where_value_index} RETURNING *'
		updated_user_record = await conn.fetchrow(query, *values, user_id)
	except Exception as e:
		raise HTTPException(status_code=500, detail={"error": f"Error updating user: {e}"})

	if updated_user_record is None:
		raise HTTPException(status_code=404, detail=f"User with user_id '{user_id}' not found.")
	
	return dict(updated_user_record)

async def get_or_create_end_user(end_user_id: str):
	async with httpx.AsyncClient() as client:
		try:
			params = {"end_user_id": end_user_id}
			response = await client.get(f"{settings.LITELLM_API_BASE}/customer/info", params=params, headers=LITELLM_HEADERS)
			end_user = response.json()
			if not end_user.get("user_id"):
				# add budget details or budget_id if necessary
				await client.post(f"{settings.LITELLM_API_BASE}/customer/new", json={"user_id": end_user_id}, headers=LITELLM_HEADERS)
				response = await client.get(f"{settings.LITELLM_API_BASE}/customer/info", params=params, headers=LITELLM_HEADERS)
				return [response.json(), True]
			return [end_user, False]
		except Exception as e:
			raise HTTPException(status_code=500, detail={"error": f"Error fetching user info: {e}"})

def main():
	uvicorn.run(app, host="0.0.0.0", port=settings.PORT, timeout_keep_alive=10)

if __name__ == "__main__":
	main()
