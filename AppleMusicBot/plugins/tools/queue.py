from pyrogram import filters
from pyrogram.types import Message

from AppleMusic import app
from AppleMusic.misc import db
from config import BANNED_USERS


@app.on_message(filters.command(["queue", "q"]) & filters.group & ~BANNED_USERS)
async def queue(_, message: Message):
    chat_id = message.chat.id
    q = db.get(chat_id) or []
    if not q:
        return await message.reply_text("Queue empty.")
    text = "**Current Queue**\n\n"
    for i, track in enumerate(q[:15], start=1):
        prefix = "▶️" if i == 1 else f"`{i}.`"
        text += f"{prefix} **{track['title']}**\n   ⏱ {track.get('duration', '?')} | {track.get('user', '')}\n"
    if len(q) > 15:
        text += f"\n...and {len(q) - 15} more"
    await message.reply_text(text)
