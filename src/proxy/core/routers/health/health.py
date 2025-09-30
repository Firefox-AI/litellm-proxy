from fastapi import APIRouter
import httpx
from ...pg_services.services import litellm_pg, app_attest_pg
from ...config import LITELLM_READINESS_URL, LITELLM_HEADERS

router = APIRouter()

@router.get("/liveness", tags=["Health"])
async def liveness_probe():
	return {"status": "alive"}

@router.get("/readiness", tags=["Health"])
async def readiness_probe():
	# todo add check to PG and LiteLLM status here
	pg_status = litellm_pg.check_status()
	app_attest_pg_status = app_attest_pg.check_status()
	litellm_status = {}
	async with httpx.AsyncClient() as client:
		response = await client.get(LITELLM_READINESS_URL, headers=LITELLM_HEADERS, timeout=3)
		data = response.json()
		litellm_status = data
	return {
		"status": "connected", 
		"pg_server_dbs": {
			 "postgres": "connected" if pg_status else "offline", 
			 "app_attest": "connected" if app_attest_pg_status else "offline", 
		},
		"litellm": litellm_status
	}