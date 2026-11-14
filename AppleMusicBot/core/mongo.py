from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_DB_URI

from ..logging import LOGGER

if not MONGO_DB_URI:
    raise RuntimeError(
        "MONGO_DB_URI is missing. Add it to your Railway environment variables."
    )

LOGGER(__name__).info("Initializing MongoDB client...")

_mongo_async_ = AsyncIOMotorClient(
    MONGO_DB_URI,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    retryWrites=True,
)

# Keep the existing database name so current collections remain unchanged.
mongodb = _mongo_async_["Anon"]
db = mongodb


async def ping_database():
    """Verify MongoDB connectivity before loading bot data."""
    try:
        await _mongo_async_.admin.command("ping")
        LOGGER(__name__).info("MongoDB connection verified successfully.")
    except Exception as exc:
        LOGGER(__name__).exception(
            f"MongoDB connection check failed: {type(exc).__name__}: {exc}"
        )
        raise
