import cbor2
import json
import time
from fastapi import HTTPException
from ...config import settings
import binascii
import os
import hashlib
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from pyattest.configs.apple import AppleConfig
from pyattest.attestation import Attestation
from pyattest.assertion import Assertion
from cryptography.x509.base import load_pem_x509_certificate
from pathlib import Path
from fastapi.concurrency import run_in_threadpool
from ...classes import AssertionRequestV2

challenge_store = {}
key_cache = {}

ROOT_CA_PEM = "Apple_App_Attestation_Root_CA.pem"
root_ca = load_pem_x509_certificate(
	Path(ROOT_CA_PEM).read_bytes()
)
root_ca_pem = root_ca.public_bytes(serialization.Encoding.PEM)
	

def generate_client_challenge(key_id: str) -> str:
	"""Create a unique challenge tied to a key ID"""
	challenge = binascii.hexlify(os.urandom(32)).decode("utf-8") # Slightly faster than secrets.token_urlsafe(32)
	challenge_store[challenge] = {
		"key_id": key_id,
		"timestamp": time.time()
	}
	return challenge

def validate_challenge(challenge: str, key_id: str) -> bool:
	"""Check that the challenge exists, is fresh, and matches key_id"""
	data = challenge_store.get(challenge)
	if not data:
		return False
	if time.time() - data["timestamp"] > settings.CHALLENGE_EXPIRY_SECONDS:
		challenge_store.pop(challenge, None)
		return False
	if data["key_id"] != key_id:
		return False
	challenge_store.pop(challenge, None)  # Invalidate challenge to prevent replay
	return True

async def get_apple_public_keys():
	return []

async def verify_attest(key_id: str, attestation_obj: str, challenge: str):
	try:
		attest = base64.urlsafe_b64decode(attestation_obj)
	except:
		raise HTTPException(status_code=400, detail="Invalid Base64 for attestationObj")
	try:
		key_id_bytes = base64.urlsafe_b64decode(key_id)
	except:
		raise HTTPException(status_code=400, detail="Invalid Base64 for keyId")
	try:
		nonce = base64.urlsafe_b64decode(challenge)
	except:
		raise HTTPException(status_code=400, detail="Invalid Base64 in payload")

	config = AppleConfig(
		key_id=key_id_bytes,
		app_id=f"{settings.APP_DEVELOPMENT_TEAM}.{settings.APP_BUNDLE_ID}",
		root_ca=root_ca_pem,
		production=False
	)

	try:
		attestation = Attestation(attest, nonce, config)
		await run_in_threadpool(attestation.verify)
		
		# Retrieve verified public key
		verified_data = attestation.data["data"]
		credential_id = verified_data["credential_id"]
		auth_data = verified_data["raw"]["authData"]
		cred_id_len = len(credential_id)
		# Offset = 37 bytes (for rpIdHash, flags, counter) + 16 (aaguid) + 2 (len) + cred_id_len
		public_key_offset = 37 + 16 + 2 + cred_id_len
		# Slice the authData to get the raw COSE public key
		cose_public_key_bytes = auth_data[public_key_offset:]
		# Decode the COSE key and convert it to PEM format.
		cose_key_obj = cbor2.loads(cose_public_key_bytes)
		# COSE Key Map for EC2 keys: 1=kty, -1=crv, -2=x, -3=y
		if cose_key_obj.get(1) != 2 or cose_key_obj.get(-1) != 1: # kty=EC2, crv=P-256
			raise ValueError("Public key is not a P-256 elliptic curve key.")
		x_coord = cose_key_obj.get(-2)
		y_coord = cose_key_obj.get(-3)

		public_key = ec.EllipticCurvePublicNumbers(
			x=int.from_bytes(x_coord, 'big'),
			y=int.from_bytes(y_coord, 'big'),
			curve=ec.SECP256R1()
		).public_key()

		public_key_pem = public_key.public_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PublicFormat.SubjectPublicKeyInfo
		).decode('utf-8')

	except Exception as e:
		raise HTTPException(status_code=403, detail=f"Attestation verification failed: {e}")
	
	# save_public_key
	key_cache[key_id_bytes] = {
		"public_key_pem": public_key_pem,
	}

	return {"status": "success"}

def verify_assert(key_id: str, assertion: str, payload: dict):
	try:
		key_id_bytes = base64.urlsafe_b64decode(key_id)
	except:
		raise HTTPException(status_code=400, detail="Invalid Base64 for key_id")
	try:
		raw_assertion = base64.urlsafe_b64decode(assertion)
	except:
		raise HTTPException(status_code=400, detail="Invalid Base64 for assertion")

	payload_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
	expected_hash = hashlib.sha256(payload_bytes).digest()

	key_info = key_cache.get(key_id_bytes)
	if not key_info:
		raise HTTPException(status_code=403, detail="Key not found for key_id")
	
	public_key_pem = key_info["public_key_pem"].encode()
	public_key_obj = serialization.load_pem_public_key(public_key_pem)
	
	config = AppleConfig(
		key_id=key_id_bytes,
		app_id=f"{settings.APP_DEVELOPMENT_TEAM}.{settings.APP_BUNDLE_ID}",
		root_ca=root_ca_pem,
		production=False
	)
	
	try:
		assertion_to_test = Assertion(raw_assertion, expected_hash, public_key_obj, config)
		assertion_to_test.verify()
	except Exception as e:
		raise HTTPException(status_code=403, detail=f"Assertion verification failed: {e}")


	return {"status": "success"}


def app_attest_auth(request: AssertionRequestV2):
	if not validate_challenge(request.challenge, request.key_id):
		return {"error": "Invalid or expired challenge"}

	try:
		return verify_assert(request.key_id, request.assertion_obj, request.payload)
	except HTTPException:
		return {"error": "Invalid App Attest session."}
	except Exception as e:
		return {"error": str(e)}
