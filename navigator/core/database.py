from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from navigator.core.config import get_settings


def get_database(app) -> AsyncIOMotorDatabase:
    if not hasattr(app.state, "navigator_mongo_client"):
        settings = get_settings()
        app.state.navigator_mongo_client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=settings.navigator_request_timeout_ms,
        )
        app.state.navigator_db = app.state.navigator_mongo_client[settings.mongodb_database]
    return app.state.navigator_db


async def ping_database(app) -> None:
    database = get_database(app)
    await database.command("ping")


async def close_database(app) -> None:
    client = getattr(app.state, "navigator_mongo_client", None)
    if client is not None:
        client.close()

