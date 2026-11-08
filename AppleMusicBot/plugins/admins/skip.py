from pyrogram import filters
from pyrogram.types import Message

from AppleMusic import app, userbot
from AppleMusic.core.call import Apple as AppleVC
from AppleMusic.misc import db
from AppleMusic.utils.decorators.admins import AdminRightsCheck
from AppleMusic.utils.stream.queue import clear_queue
from config import BANNED_USERS


@app.on_message(filters.command(["skip", "cskip", "next"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def skip_cmd(_, message: Message):
    chat_id = message.chat.id
    q = db.get(chat_id) or []
    assistant = userbot.assistants[0]
    try:
        if len(q) <= 1:
            await AppleVC.leave(assistant, chat_id)
            await clear_queue(chat_id)
            return await message.reply_text("Queue finished. Left VC.")
        q.pop(0)
        nxt = q[0]
        await AppleVC.change_stream(
            assistant,
            chat_id,
            nxt["path"],
            video=nxt.get("stream_type") == "video",
        )
        await message.reply_text(
            f"⏭ Skipped by {message.from_user.mention}\n"
            f"▶ **Now:** {nxt['title']}"
        )
    except Exception as e:
        await message.reply_text(f"Failed: `{e}`")
