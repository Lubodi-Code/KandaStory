from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None

async def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.DB_URI)
    return _client

async def get_db() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        client = await get_client()
        _db = client[settings.DB_NAME]
    return _db

async def close_db():
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
