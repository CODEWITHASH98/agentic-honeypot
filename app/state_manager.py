import json
import redis.asyncio as redis
from app.config import settings

class InMemoryBackend:
    def __init__(self):
        self.data = {}
        print("WARNING: Using InMemoryBackend (Redis unavailable)")

    async def get(self, key):
        return self.data.get(key)
    
    async def setex(self, key, ttl, value):
        self.data[key] = value
    
    async def close(self):
        pass

class StateManager:
    def __init__(self):
        self.redis = None
        self.memory = None
        self.ttl = 3600

    async def _ensure_backend(self):
        if self.redis:
            return self.redis
        if self.memory:
            return self.memory
            
        try:
            r = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.ping()
            self.redis = r
            print("Connected to Redis")
            return self.redis
        except Exception as e:
            print(f"Redis connection failed: {e}. Falling back to in-memory.")
            self.memory = InMemoryBackend()
            return self.memory

    async def get_session(self, conversation_id: str):
        backend = await self._ensure_backend()
        data = await backend.get(conversation_id)
        if data:
            return json.loads(data)
        return None

    async def save_session(self, conversation_id: str, data: dict):
        backend = await self._ensure_backend()
        await backend.setex(conversation_id, self.ttl, json.dumps(data))

    async def close(self):
        if self.redis:
            await self.redis.close()

state_manager = StateManager()
