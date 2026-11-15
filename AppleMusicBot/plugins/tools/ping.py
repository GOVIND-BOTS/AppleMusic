from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app
from AppleMusicBot.core.call import AppleBot
from AppleMusicBot.logging import LOGGER
from AppleMusicBot.utils.sys import bot_sys_stats


@app.on_message(filters.command(["ping", "alive"]))
async def ping_com(client, message: Message):
    LOGGER(__name__).info(f"Ping command received from {message.from_user.id if message.from_user else 'Unknown'} in chat {message.chat.id}")
    
    try:
        started_at = datetime.now()
        response = await message.reply_text("🏓 Pong! Checking...")
        
        try:
            pytgping = await AppleBot.ping()
        except Exception as exc:
            LOGGER(__name__).warning(f"PyTgCalls ping failed: {exc}")
            pytgping = "N/A"
            
        try:
            up, cpu, ram, disk = await bot_sys_stats()
        except Exception as exc:
            LOGGER(__name__).warning(f"System stats failed: {exc}")
            up, cpu, ram, disk = "N/A", "N/A", "N/A", "N/A"
            
        latency = (datetime.now() - started_at).total_seconds() * 1000
        
        await response.edit_text(
            f"🏓 **PONG!**\n\n"
            f"**Bot:** {app.mention}\n"
            f"**Latency:** `{latency:.2f} ms`\n"
            f"**Uptime:** `{up}`\n"
            f"**CPU:** `{cpu}`\n"
            f"**RAM:** `{ram}`\n"
            f"**Disk:** `{disk}`\n"
            f"**Voice Engine:** `{pytgping}`",
            disable_web_page_preview=True,
        )
        
    except Exception as e:
        LOGGER(__name__).exception("Ping command completely failed")
        try:
            await message.reply_text(f"❌ Ping Error: `{type(e).__name__}: {str(e)[:200]}`")
        except:
            pass
