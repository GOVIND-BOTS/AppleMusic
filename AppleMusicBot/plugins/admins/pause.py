from pyrogram import filters
from pyrogram.types import Message

from AppleMusic import app, userbot
from AppleMusic.core.call import Apple as AppleVC
from AppleMusic.utils.decorators.admins import AdminRightsCheck
from config import BANNED_USERS


@app.on_message(filters.command(["pause", "cpause"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def pause_cmd(_, message: Message):
    try:
        await AppleVC.pause(userbot.assistants[0], message.chat.id)
        await message.reply_text(f"⏸ Paused by {message.from_user.mention}")
    except Exception as e:
        await message.reply_text(f"Failed: `{e}`")
