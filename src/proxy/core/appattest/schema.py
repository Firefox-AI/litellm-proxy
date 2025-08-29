from pydantic import BaseModel

class AttestationRequest(BaseModel):
    token: str
    challenge: str
    device_id: str

class AttestationRequestV2(BaseModel):
    key_id: str
    attestation_obj: str
    challenge: str
    device_id: str

class AssertionRequestV2(BaseModel):
    user_id: str
    key_id: str
    assertion: str
    payload: dict
    # client_data_hash: str
    # device_id: str
    # challenge: str