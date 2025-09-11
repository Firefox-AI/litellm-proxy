from typing import Annotated
from fastapi import Header, APIRouter, Query
from fxa.oauth import Client
from ...config import settings

router = APIRouter()
client = Client()

@router.get("/callback", tags=["FxA"])
def fxa_callback(code: str = Query(...)):
	try:
		token = client.trade_code(
			settings.CLIENT_ID, 
			settings.CLIENT_SECRET, 
			code
		)
	except:
		return {"error": f"Invalid FxA code"}
	return {"access_token": token}

def fxa_auth(authorization: Annotated[str | None, Header()]):
	try:
		profile = client.verify_token(authorization)
	except Exception:
		return {"error": "Invalid FxA auth"}
	return profile