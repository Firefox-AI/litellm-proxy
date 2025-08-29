import cbor2
import json
import time
from fastapi import HTTPException, Header
from jose import jwt, JWTError
from .config import settings
import binascii
import os
import hashlib
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from pyattest.configs.apple import AppleConfig
from pyattest.attestation import Attestation
from pyattest.assertion import Assertion
from cryptography.x509.base import load_pem_x509_certificate
from pathlib import Path
from fastapi.concurrency import run_in_threadpool

challenge_store = {}
key_cache = {}

ROOT_CA_PEM = "src/proxy/core/appattest/Apple_App_Attestation_Root_CA.pem"
root_ca = load_pem_x509_certificate(
	Path(ROOT_CA_PEM).read_bytes()
)
root_ca_pem = root_ca.public_bytes(serialization.Encoding.PEM)
	

def generate_client_challenge(device_id: str) -> str:
	"""Create a unique challenge tied to a device ID"""
	challenge = binascii.hexlify(os.urandom(32)).decode("utf-8") # Slightly faster than secrets.token_urlsafe(32)
	challenge_store[challenge] = {
		"device_id": device_id,
		"timestamp": time.time()
	}
	return challenge

def validate_challenge(challenge: str, device_id: str) -> bool:
	"""Check that the challenge exists, is fresh, and matches device"""
	data = challenge_store.get(challenge)
	if not data:
		return False
	if time.time() - data["timestamp"] > settings.CHALLENGE_EXPIRY_SECONDS:
		challenge_store.pop(challenge, None)
		return False
	if data["device_id"] != device_id:
		return False
	challenge_store.pop(challenge, None)  # Invalidate challenge to prevent replay
	return True

def issue_attested_session_token(device_id: str) -> str:
	payload = {
		"device_id": device_id,
		"iat": int(time.time()),
		"exp": int(time.time()) + settings.JWT_EXPIRY_SECONDS,
		"type": "attested_session"
	}
	return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

async def get_apple_public_keys():
	return []

async def verify_attestation_token(token: str, expected_device_id: str, expected_challenge: str):
	keys = await get_apple_public_keys()
	for key in keys:
		try:
			payload = jwt.decode(
				token,
				key,
				algorithms=["ES256"],
				audience=settings.APP_BUNDLE_ID,
				options={"verify_exp": True}
			)

			if payload.get("app_id") != settings.APP_BUNDLE_ID or \
			   payload.get("device_id") != expected_device_id or \
			   payload.get("challenge") != expected_challenge:
				raise ValueError("Invalid token payload")

			return payload

		except JWTError:
			continue
		except ValueError as ve:
			raise ve
	raise ValueError("Failed attestation validation")

async def verify_attest_v2(key_id: str, attestation_obj: str, challenge: str):
	attest = base64.urlsafe_b64decode(attestation_obj)
	key_id_bytes = base64.urlsafe_b64decode(key_id)
	nonce = base64.urlsafe_b64decode(challenge)

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
		"sign_count": 0
	}

	return {"status": "success"}

def verify_assert_v2(key_id: str, assertion: str, payload: dict):
	try:
		key_id_bytes = base64.urlsafe_b64decode(key_id)
		raw_assertion = base64.urlsafe_b64decode(assertion)
	except Exception:
		raise HTTPException(status_code=400, detail="Invalid Base64 for keyId or assertion")

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
	
	# try:
	assertion_to_test = Assertion(raw_assertion, expected_hash, public_key_obj, config)
	assertion_to_test.verify()
	# except Exception as e:
	# 	raise HTTPException(status_code=403, detail=f"Assertion verification failed: {e}")

	# should update the sign count here
	# key_info['sign_count'] = result['sign_count']
	# key_cache[key_id_bytes] = key_info

	return {"status": "success"}
