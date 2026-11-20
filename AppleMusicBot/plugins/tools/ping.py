from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app
from AppleMusicBot.core.call import AppleBot
from AppleMusicBot.logging import LOGGER
from AppleMusicBot.utils.sys import bot_sys_stats


# Low-priority diagnostic: records that Telegram delivered a message update
# to this process without logging the message text or other private content.
@app.on_message(filters.all, group=-100)
async def incoming_message_probe(_, message: Message):
    sender = message.from_user.id if message.from_user else "unknown"
    chat_id = message.chat.id if message.chat else "unknown"
    LOGGER(__name__).info(
        "INCOMING MESSAGE UPDATE | sender=%s | chat=%s | type=%s",
        sender,
        chat_id,
        message.chat.type if message.chat else "unknown",
    )


@app.on_message(filters.command(["ping", "alive"]) & ~filters.forwarded)
async def ping_com(_, message: Message):
    LOGGER(__name__).info(
        "PING TRIGGERED | User: %s | Chat: %s",
        message.from_user.id if message.from_user else "N/A",
        message.chat.id,
    )

    try:
        start = datetime.now()
        reply = await message.reply_text("🏓 Pong...")

        try:
            pytg = await AppleBot.ping()
        except Exception as exc:
            LOGGER(__name__).warning("PyTgCalls ping failed: %s", exc)
            pytg = "N/A"

        try:
            up, cpu, ram, disk = await bot_sys_stats()
        except Exception as exc:
            LOGGER(__name__).warning("System stats unavailable: %s", exc)
            up = cpu = ram = disk = "N/A"

        latency = (datetime.now() - start).total_seconds() * 1000
        await reply.edit_text(
            f"🏓 **PONG**\n\n"
            f"**Latency:** `{latency:.2f} ms`\n"
            f"**Uptime:** `{up}`\n"
            f"**CPU:** `{cpu}`\n"
            f"**RAM:** `{ram}`\n"
            f"**Disk:** `{disk}`\n"
            f"**PyTgCalls:** `{pytg}`"
        )
    except Exception:
        LOGGER(__name__).exception("Ping handler failed.")
        try:
            await message.reply_text("⚠️ Ping handler error. Check Railway logs.")
        except Exception:
            LOGGER(__name__).exception("Could not send ping error reply.")
