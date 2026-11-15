from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app
from AppleMusicBot.core.call import AppleBot
from AppleMusicBot.logging import LOGGER
from AppleMusicBot.utils.sys import bot_sys_stats


@app.on_message(filters.command(["ping", "alive"]) & ~filters.forwarded)
async def ping_com(_, message: Message):
    LOGGER(__name__).info(f"PING TRIGGERED | User: {message.from_user.id if message.from_user else 'N/A'} | Chat: {message.chat.id}")
    
    try:
        start = datetime.now()
        m = await message.reply_text("🏓 Pong...")

        try:
            pytg = await AppleBot.ping()
        except:
            pytg = "N/A"

        try:
            up, cpu, ram, disk = await bot_sys_stats()
        except:
            up = cpu = ram = disk = "N/A"

        end = datetime.now()
        latency = (end - start).total_seconds() * 1000

        await m.edit_text(
            f"🏓 **PONG**\n\n"
            f"**Latency:** `{latency:.2f} ms`\n"
            f"**Uptime:** `{up}`\n"
            f"**CPU:** `{cpu}`\n"
            f"**RAM:** `{ram}`\n"
            f"**Disk:** `{disk}`\n"
            f"**PyTgCalls:** `{pytg}`"
        )
    except Exception as e:
        LOGGER(__name__).error(f"Ping Error: {e}")
        try:
            await message.reply_text(f"Error: `{e}`")
        except:
            pass
