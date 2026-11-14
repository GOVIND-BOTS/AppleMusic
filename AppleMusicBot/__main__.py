import asyncio
import importlib

from pyrogram import idle

import config
from AppleMusicBot import LOGGER, app, userbot
from AppleMusicBot.core.call import AppleBot as AppleCall
from AppleMusicBot.core.mongo import ping_database
from AppleMusicBot.misc import heroku, sudo
from AppleMusicBot.plugins import ALL_MODULES
from AppleMusicBot.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def shutdown():
    """Stop all started clients safely."""
    LOGGER("AppleMusicBot").info("Shutting down AppleMusic...")

    try:
        await AppleCall.stop()
    except Exception as exc:
        LOGGER("AppleMusicBot").warning(
            f"PyTgCalls shutdown warning: {type(exc).__name__}: {exc}"
        )

    try:
        await userbot.stop()
    except Exception as exc:
        LOGGER("AppleMusicBot").warning(
            f"Userbot shutdown warning: {type(exc).__name__}: {exc}"
        )

    try:
        await app.stop()
    except Exception as exc:
        LOGGER("AppleMusicBot").warning(
            f"Bot shutdown warning: {type(exc).__name__}: {exc}"
        )


async def init():
    try:
        await ping_database()
        heroku()
        await sudo()

        try:
            for user_id in await get_gbanned():
                BANNED_USERS.add(user_id)
            for user_id in await get_banned_users():
                BANNED_USERS.add(user_id)
        except Exception as exc:
            LOGGER(__name__).warning(
                f"Failed to load banned users: {type(exc).__name__}: {exc}"
            )

        await app.start()
        LOGGER("AppleMusicBot").info("Bot client started.")

        for module in ALL_MODULES:
            if module.startswith("AppleMusicBot.plugins"):
                importlib.import_module(module)
            else:
                importlib.import_module(
                    "AppleMusicBot.plugins." + module.lstrip(".")
                )

        LOGGER("AppleMusicBot.plugins").info(
            "Successfully imported all plugins."
        )

        await userbot.start()
        LOGGER("AppleMusicBot").info("Userbot startup completed.")

        await AppleCall.start()
        LOGGER("AppleMusicBot").info(
            "AppleMusic Bot Started Successfully."
        )
        await idle()

    except KeyboardInterrupt:
        LOGGER("AppleMusicBot").info("Shutdown requested.")
    except Exception:
        LOGGER(__name__).exception("Startup/runtime error.")
        raise
    finally:
        await shutdown()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(init())
    except KeyboardInterrupt:
        LOGGER("AppleMusicBot").info("Process interrupted.")
    finally:
        asyncio.set_event_loop(loop)
