import base64
from .config import LITELLM_COMPLETIONS_URL, LITELLM_HEADERS, env
import httpx
from fastapi import HTTPException

async def completion(prompt: str, end_user_id: str):
	body = {
		"model": env.MODEL_NAME, 
		"messages": [
			{"role": "system", "content": env.SYSTEM_PROMPT},
			{"role": "user", "content": prompt},
		],
		"temperature": env.TEMPERATURE,
		"top_p": env.TOP_P,
		"max_tokens": env.MAX_COMPLETION_TOKENS,
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
			response = await client.get(f"{env.LITELLM_API_BASE}/customer/info", params=params, headers=LITELLM_HEADERS)
			end_user = response.json()
			if not end_user.get("user_id"):
				# add budget details or budget_id if necessary
				await client.post(f"{env.LITELLM_API_BASE}/customer/new", json={"user_id": end_user_id}, headers=LITELLM_HEADERS)
				response = await client.get(f"{env.LITELLM_API_BASE}/customer/info", params=params, headers=LITELLM_HEADERS)
				return [response.json(), True]
			return [end_user, False]
		except Exception as e:
			raise HTTPException(status_code=500, detail={"error": f"Error fetching user info: {e}"})

def b64decode_safe(data_b64: str, obj_name: str="object") -> str:
	try:
		return base64.urlsafe_b64decode(data_b64)
	except Exception as e:
		raise HTTPException(status_code=400, detail={obj_name: f"Invalid Base64: {e}"})
	