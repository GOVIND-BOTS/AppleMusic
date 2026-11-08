import asyncio
import importlib

from pyrogram import idle

from AppleMusicBot import LOGGER, app, userbot
from AppleMusicBot.core.call import Apple
from AppleMusicBot.misc import sudo
from AppleMusicBot.plugins import ALL_MODULES
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

    LOGGER(__name__).info("AppleMusicBot  is running.")
    await idle()

    await app.stop()
    await userbot.stop()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
