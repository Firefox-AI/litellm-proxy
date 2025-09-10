from fastapi import APIRouter

router = APIRouter()

@router.get("/liveness", tags=["Health"])
async def liveness_probe():
	return {"status": "alive"}