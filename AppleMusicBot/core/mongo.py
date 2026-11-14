from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_DB_URI

from ..logging import LOGGER


if not MONGO_DB_URI:
    raise RuntimeError(
        "Missing required environment variable: MONGO_DB_URI. "
        "Add your MongoDB connection URI to the hosting environment."
    )

LOGGER(__name__).info("Initializing MongoDB client...")

# Motor connects lazily. A successful constructor alone does not prove that
# the database is reachable, so the actual ping is performed asynchronously.
_mongo_async_ = AsyncIOMotorClient(
    MONGO_DB_URI,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
)

mongodb = _mongo_async_.Anon
db = mongodb


async def ping_mongo():
    """Verify MongoDB connectivity before the bot starts using collections."""
    try:
        await _mongo_async_.admin.command("ping")
    except Exception as exc:
        LOGGER(__name__).error(
            f"MongoDB connection check failed: {type(exc).__name__}: {exc}"
        )
        raise RuntimeError(
            "Could not connect to MongoDB. Check MONGO_DB_URI, "
            "network access, and MongoDB IP allow-list settings."
        ) from exc

    LOGGER(__name__).info("MongoDB connection verified.")


# Backward-compatible name used by the startup module.
ping_database = ping_mongo
