
from fastapi import APIRouter, HTTPException
from .appattest import (
    generate_client_challenge,
    verify_assert_v2,
    verify_attestation_token,
    issue_attested_session_token,
    validate_challenge,
    verify_attest_v2
)
from .schema import AssertionRequestV2, AttestationRequest, AttestationRequestV2


router = APIRouter()


@router.get("/challenge")
def get_challenge(device_id: str):
    if not device_id:
        raise HTTPException(status_code=400, detail="Missing device_id")
    return {"challenge": generate_client_challenge(device_id)}

@router.post("/attest")
async def attest(request: AttestationRequest):
    if not validate_challenge(request.challenge, request.device_id):
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")


    try:
        await verify_attestation_token(request.token, request.device_id, request.challenge)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    token = issue_attested_session_token(request.device_id)
    return {"status": "attestation_success", "session_token": token}

@router.post("/attest_v2")
async def attest_v2(request: AttestationRequestV2):
    if not validate_challenge(request.challenge, request.device_id):
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")

    try:
        result = await verify_attest_v2(request.key_id, request.attestation_obj, request.challenge)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return result

@router.post("/assert_v2")
async def assert_v2(request: AssertionRequestV2):
    try:
        result = await verify_assert_v2(request.key_id, request.assertion, request.payload)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    # token = issue_attested_session_token(request.device_id)
    # return {"status": "assertion_success", "session_token": token}
    return result