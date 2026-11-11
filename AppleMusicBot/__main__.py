
import asyncio
import importlib

from pyrogram import idle

import config
from AppleMusicBot import LOGGER, app, userbot
from AppleMusicBot.core.call import AppleBot as AppleCall
from AppleMusicBot.misc import sudo
from AppleMusicBot.plugins import ALL_MODULES
from AppleMusicBot.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def shutdown():
    """Stop all started clients safely."""

    LOGGER("AppleMusicBot").info("Shutting down AppleMusic...")

    try:
        await AppleCall.stop()
    except Exception as e:
        LOGGER("AppleMusicBot").warning(
            f"PyTgCalls shutdown warning: {type(e).__name__}: {e}"
        )

    try:
        await userbot.stop()
    except Exception as e:
        LOGGER("AppleMusicBot").warning(
            f"Userbot shutdown warning: {type(e).__name__}: {e}"
        )

    try:
        await app.stop()
    except Exception as e:
        LOGGER("AppleMusicBot").warning(
            f"Bot shutdown warning: {type(e).__name__}: {e}"
        )

    LOGGER("AppleMusicBot").info("Shutdown completed.")


async def init():
    started = False

    try:
        if not any([
            config.STRING1,
            config.STRING2,
            config.STRING3,
            config.STRING4,
            config.STRING5,
        ]):
            LOGGER(__name__).error(
                "Assistant client variables not defined, exiting..."
            )
            return

        await sudo()

        try:
            users = await get_gbanned()
            for user_id in users:
                BANNED_USERS.add(user_id)

            users = await get_banned_users()
            for user_id in users:
                BANNED_USERS.add(user_id)

        except Exception as e:
            LOGGER(__name__).warning(
                f"Failed to load banned users: {e}"
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
        LOGGER("AppleMusicBot").info("Userbot started.")

        await AppleCall.start()
        started = True

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
        # Keep the loop available for PyTgCalls atexit cleanup.
        asyncio.set_event_loop(loop)
