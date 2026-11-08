import asyncio
import importlib

from pyrogram import idle

from AppleMusic import LOGGER, app, userbot
from AppleMusic.core.call import Apple
from AppleMusic.misc import sudo
from AppleMusic.plugins import ALL_MODULES
from config import OWNER_ID


async def init():
    if OWNER_ID:
        sudo["owners"] = [OWNER_ID]

    await app.start()

    for module in ALL_MODULES:
        importlib.import_module(module)
        LOGGER(__name__).info(f"Loaded: {module}")

    await userbot.start()
    await Apple.start(userbot.assistants)

    LOGGER(__name__).info("AppleMusic bot is running.")
    await idle()

    await app.stop()
    await userbot.stop()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
