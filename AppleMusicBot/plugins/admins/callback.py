from pyrogram import filters
from pyrogram.types import CallbackQuery

from AppleMusicBot import app, userbot
from AppleMusicBot.core.call import Apple as AppleVC
from AppleMusicBot.misc import db
from AppleMusicBot.utils.decorators.admins import AdminRightsCheck
from AppleMusicBot.utils.stream.queue import clear_queue


def _assistant():
    return userbot.assistants[0]


@app.on_callback_query(filters.regex(r"^am_(pause|resume|skip|stop)$"))
async def am_controls(_, query: CallbackQuery):
    if not query.message:
        return await query.answer("Message unavailable.", show_alert=True)

    chat_id = query.message.chat.id
    action = query.data.split("_", 1)[1]
    assistant = _assistant()
    q = db.get(chat_id) or []

    try:
        if action == "pause":
            await AppleVC.pause(assistant, chat_id)
            await query.answer("Paused")
            return await query.message.reply_text(
                f"⏸ Paused by {query.from_user.mention}"
            )

        if action == "resume":
            await AppleVC.resume(assistant, chat_id)
            await query.answer("Resumed")
            return await query.message.reply_text(
                f"▶️ Resumed by {query.from_user.mention}"
            )

        if action == "stop":
            await AppleVC.leave(assistant, chat_id)
            await clear_queue(chat_id)
            await query.answer("Stopped")
            return await query.message.reply_text(
                f"⏹ Stopped by {query.from_user.mention}"
            )

        if action == "skip":
            if len(q) <= 1:
                await AppleVC.leave(assistant, chat_id)
                await clear_queue(chat_id)
                await query.answer("Queue finished")
                return await query.message.reply_text("Queue finished.")
            q.pop(0)
            nxt = q[0]
            video = nxt.get("stream_type") == "video"
            await AppleVC.change_stream(
                assistant,
                chat_id,
                nxt["path"],
                video=video,
            )
            await query.answer("Skipped")
            return await query.message.reply_text(
                f"⏭ Skipped\n▶ **Now:** {nxt['title']}"
            )
    except Exception as e:
        await query.answer(str(e)[:80], show_alert=True)
