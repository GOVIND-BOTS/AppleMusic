from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app
from AppleMusicBot.core.call import AppleBot
from AppleMusicBot.logging import LOGGER
from AppleMusicBot.utils.sys import bot_sys_stats
from AppleMusicBot.utils.inline import supp_markup


@app.on_message(filters.command(["ping", "alive"]))
async def ping_com(client, message: Message):
    started_at = datetime.now()
    # Reply immediately; diagnostics must not depend on MongoDB or language lookup.
    try:
        response = await message.reply_text("🏓 Pong! Checking bot status…")
        try:
            pytgping = await AppleBot.ping()
        except Exception as exc:
            LOGGER(__name__).warning("PyTgCalls ping failed: %s: %s", type(exc).__name__, exc)
            pytgping = "N/A"
        try:
            up, cpu, ram, disk = await bot_sys_stats()
        except Exception as exc:
            LOGGER(__name__).warning("System stats failed: %s: %s", type(exc).__name__, exc)
            up, cpu, ram, disk = "N/A", "N/A", "N/A", "N/A"
        latency = (datetime.now() - started_at).total_seconds() * 1000
        await response.edit_text(
            "🏓 PONG!\n\n"
            f"Bot: {app.mention}\n"
            f"Latency: {latency:.2f} ms\n"
            f"Uptime: {up}\nCPU: {cpu}\nRAM: {ram}\nDisk: {disk}\n"
            f"Voice engine: {pytgping}",
            reply_markup=supp_markup(None),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        LOGGER(__name__).exception("Ping command failed")
        try:
            await message.reply_text(
                f"Ping handler error: {type(exc).__name__}: {str(exc)[:250]}"
            )
        except Exception:
            pass
