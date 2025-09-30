from typing import Annotated
from fastapi import Header, APIRouter
from fxa.oauth import Client
from ...config import env

router = APIRouter()
fxa_url = "https://api-accounts.stage.mozaws.net/v1" if env.DEBUG else "https://oauth.accounts.firefox.com/v1"
client = Client(env.CLIENT_ID, env.CLIENT_SECRET, fxa_url)

def fxa_auth(x_fxa_authorization: Annotated[str | None, Header()]):
	token = x_fxa_authorization.removeprefix("Bearer ").split()[0]
	try:
		profile = client.verify_token(token, scope="profile")
	except Exception as e:
		return {"error": f"Invalid FxA auth: {e}"}
	return profile