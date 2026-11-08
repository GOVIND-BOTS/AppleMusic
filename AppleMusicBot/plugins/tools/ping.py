import time

from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app
from AppleMusicBot.misc import START_TIME
from AppleMusicBot.utils.formatters import get_readable_time
from config import BANNED_USERS


@app.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
async def ping(_, message: Message):
    start = time.time()
    msg = await message.reply_text("Pinging...")
    end = time.time()
    uptime = get_readable_time(int(time.time() - START_TIME))
    await msg.edit_text(
        f"**Pong!** `{round((end - start) * 1000)}ms`\n"
        f"**Uptime:** `{uptime}`"
    )
