from ..config import settings
from .pg_service import PGService

class KeyPGService(PGService):
	def __init__(self):
		super().__init__(settings.KEY_DB_NAME)

	async def store_key(self, key_id: str, public_key: str):
		if not self.connected:
			raise ValueError("Database not connected")

		try:
			await self.pg.execute("INSERT INTO app_attest_public_keys (key_id, public_key) VALUES ($1, $2)", key_id, public_key)
		except Exception as e:
			print(f"Error storing key: {e}")

	async def get_key(self, key_id: str) -> str | None:
		if not self.connected:
			raise ValueError("Database not connected")

		try:
			record = await self.pg.fetchrow("SELECT public_key FROM app_attest_public_keys WHERE key_id = $1", key_id)
			if record:
				return record["public_key"]
			return None
		except Exception as e:
			print(f"Error retrieving key: {e}")
			return None
