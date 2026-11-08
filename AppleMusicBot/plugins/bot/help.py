from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app
from config import BANNED_USERS, BOT_NAME


@app.on_message(filters.command(["help"]) & filters.group & ~BANNED_USERS)
async def help_group(_, message: Message):
    await message.reply_text(
        f"**🍎 {BOT_NAME} Commands**\n\n"
        "**Play**\n"
        "`/play <name|url>` — audio\n"
        "`/vplay <name|url>` — video\n\n"
        "**Controls**\n"
        "`/pause` `/resume` `/skip` `/stop`\n"
        "`/queue`\n\n"
        "**Platforms**\n"
        "YouTube • Spotify • Apple Music\n"
        "SoundCloud • Resso • Telegram files"
    )
