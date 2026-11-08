from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app, userbot
from AppleMusicBot.core.call import Apple as AppleVC
from AppleMusicBot.utils.decorators.admins import AdminRightsCheck
from AppleMusicBot.utils.stream.queue import clear_queue
from config import BANNED_USERS


@app.on_message(
    filters.command(["stop", "end", "cstop", "cend"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def stop_cmd(_, message: Message):
    try:
        await AppleVC.leave(userbot.assistants[0], message.chat.id)
        await clear_queue(message.chat.id)
        await message.reply_text(f"⏹ Stopped by {message.from_user.mention}")
    except Exception as e:
        await message.reply_text(f"Failed: `{e}`")
