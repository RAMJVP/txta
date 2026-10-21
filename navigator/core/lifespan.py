from contextlib import asynccontextmanager
from navigator.core.config import get_settings

@asynccontextmanager
async def lifespan(app):
    s=get_settings(); client=None
    if s.mongodb_uri:
        from motor.motor_asyncio import AsyncIOMotorClient
        client=AsyncIOMotorClient(s.mongodb_uri, serverSelectionTimeoutMS=1500, connectTimeoutMS=1500, maxPoolSize=30)
        app.state.mongo_client=client; app.state.db=client[s.mongodb_database]
    else:
        app.state.mongo_client=None; app.state.db=None
    yield
    if client: client.close()
