from fastapi import APIRouter, HTTPException, Depends
from .appattest import (
    generate_client_challenge,
    validate_challenge,
    verify_attest
)
from ...classes import AttestationRequestV2

router = APIRouter()

@router.get("/challenge", tags=["App Attest"])
def get_challenge(key_id: str):
    if not key_id:
        raise HTTPException(status_code=400, detail="Missing key_id")
    return {"challenge": generate_client_challenge(key_id)}

@router.post("/attest", tags=["App Attest"])
async def attest(request: AttestationRequestV2):
    if not validate_challenge(request.challenge, request.key_id):
        raise HTTPException(status_code=400, detail="Invalid or expired challenge")

    try:
        result = await verify_attest(request.key_id, request.attestation_obj, request.challenge)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return result
