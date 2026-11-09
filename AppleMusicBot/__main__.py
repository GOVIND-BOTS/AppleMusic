import asyncio
import importlib

from pyrogram import idle

import config
from AppleMusicBot import LOGGER, app, userbot
from AppleMusicBot.misc import sudo
from AppleMusicBot.plugins import ALL_MODULES
from AppleMusicBot.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
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
        LOGGER(__name__).warning(f"Failed to load banned users: {e}")

    await app.start()

    LOGGER("AppleMusicBot").info("Bot client started.")

    for all_module in ALL_MODULES:
        importlib.import_module(
            "AppleMusicBot.plugins." + all_module
        )

    LOGGER("AppleMusicBot.plugins").info(
        "Successfully Imported Modules..."
    )

    await userbot.start()

    LOGGER("AppleMusicBot").info(
        "Userbot started successfully."
    )

    LOGGER("AppleMusicBot").info(
        "AppleMusic Bot Started Successfully."
    )

    try:
        await idle()

    finally:
        await userbot.stop()
        await app.stop()

        LOGGER("AppleMusicBot").info(
            "AppleMusic Bot Stopped Successfully."
        )


if __name__ == "__main__":
    asyncio.run(init())
