from fastapi import APIRouter, HTTPException
from ...pg_services.services import litellm_pg

router = APIRouter()


@router.get("/{user_id}", tags=["User"])
async def user_info(user_id: str):
	if not user_id:
		raise HTTPException(status_code=400, detail="Missing user_id")
	user = await litellm_pg.get_user(user_id)
	if not user:
		raise HTTPException(status_code=404, detail="User not found")
	return {"user": user}
