from typing import Any, Dict, Optional
from pydantic import BaseModel
from .config import env

DEBUG = env.DEBUG

class MessagesPayload(BaseModel):
	payload: Dict[str, Any] = {}

class UserUpdatePayload(BaseModel):
	user_id: str
	alias: str | None = None
	budget_id: str | None = None
	blocked: bool | None = None

class AttestationRequest(BaseModel):
    key_id: str
    challenge_b64: str
    attestation_obj_b64: str
	
class AssertionRequest(BaseModel):
    key_id: Optional[str] = None
    challenge_b64: Optional[str] = None
    assertion_obj_b64: Optional[str] = None
    payload: Optional[dict] = None