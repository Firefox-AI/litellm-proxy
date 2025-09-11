from collections import defaultdict
import json
from typing import Any, Dict, Optional
from pydantic import BaseModel
import time
from .config import settings

DEBUG = settings.DEBUG

class MessagesPayload(BaseModel):
	payload: Dict[str, Any] = {}

class UserUpdatePayload(BaseModel):
	user_id: str
	alias: str | None = None
	budget_id: str | None = None
	blocked: bool | None = None

class Timer:
	def __init__(self):
		if DEBUG:
			self._start_time = None
			self._checkpoints = defaultdict(list)
		
	def start(self):
		if DEBUG:
			self._start_time = time.time()
			self._checkpoints.clear()

	def checkpoint(self, name: str):
		if DEBUG:
			if self._start_time is None:
				raise ValueError("Timer has not been started.")
			elapsed = time.time() - self._start_time
			self._checkpoints[name].append(elapsed)
	
	def get_results(self):
		if DEBUG:
			return dict(self._checkpoints)
		return {}
	
	def get_total_time(self):
		if DEBUG:
			return sum(sum(times) for [key, times] in self._checkpoints.items() if key != "total")
		return 0
	
	def log(self):
		if DEBUG:
			with open(settings.METRICS_LOG_FILE, "a") as f:
				f.write(self.__str__() + "\n")
			print(self)

	def __str__(self):
		if DEBUG:
			total = self.get_total_time()
			self._checkpoints["total"] = [total]
			results = self.get_results()
			del self._checkpoints["total"]
			return json.dumps(results)
		return ""

class AttestationRequest(BaseModel):
    key_id: str
    challenge_b64: str
    attestation_obj_b64: str
	
class AssertionRequest(BaseModel):
    key_id: Optional[str] = None
    challenge_b64: Optional[str] = None
    assertion_obj_b64: Optional[str] = None
    payload: Optional[dict] = None