from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app, userbot
from AppleMusicBot.core.call import Apple as AppleVC
from AppleMusicBot.utils.decorators.admins import AdminRightsCheck
from config import BANNED_USERS


@app.on_message(filters.command(["resume", "cresume"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def resume_cmd(_, message: Message):
    try:
        await AppleVC.resume(userbot.assistants[0], message.chat.id)
        await message.reply_text(f"▶️ Resumed by {message.from_user.mention}")
    except Exception as e:
        await message.reply_text(f"Failed: `{e}`")
