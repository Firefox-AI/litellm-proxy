from .config import settings
from .classes import UserUpdatePayload
import httpx
import asyncpg
from fastapi import HTTPException, Header

LITELLM_COMPLETIONS_URL = f"{settings.LITELLM_API_BASE}/v1/chat/completions"
LITELLM_HEADERS = {
	"Content-Type": "application/json",
	"X-LiteLLM-Key": f"Bearer {settings.MASTER_KEY}"
}

async def completion(prompt: str, end_user_id: str):
	body = {
		"model": settings.MODEL_NAME, 
		"messages": [
            {"role": "system", "content": settings.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
		"temperature": settings.TEMPERATURE,
		"top_p": settings.TOP_P,
		"max_tokens": settings.MAX_COMPLETION_TOKENS,
		"user": end_user_id
	}
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