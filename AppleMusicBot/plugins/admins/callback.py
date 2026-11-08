
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import CallbackQuery

from AppleMusicBot import app, userbot
from AppleMusicBot.core.call import Apple as AppleVC
from AppleMusicBot.utils.stream.queue import (
    clear_queue,
    get_current_track,
    pop_current,
)
from config import OWNER_ID


async def is_admin(chat_id: int, user_id: int):
    if user_id == OWNER_ID:
        return True

    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


@app.on_callback_query(
    filters.regex(r"^am_(pause|resume|skip|stop)$")
)
async def am_controls(_, query: CallbackQuery):
    if not query.message:
        return await query.answer(
            "Message unavailable.",
            show_alert=True,
        )

    chat_id = query.message.chat.id
    action = query.data.split("_", 1)[1]

    if not await is_admin(chat_id, query.from_user.id):
        return await query.answer(
            "Only admins can use music controls.",
            show_alert=True,
        )

    if not userbot.assistants:
        return await query.answer(
            "No assistant available.",
            show_alert=True,
        )

    assistant = userbot.assistants[0]

    try:
        if action == "pause":
            await AppleVC.pause(assistant, chat_id)
            await query.answer("Music paused.")
            return await query.message.reply_text(
                f"⏸ Paused by {query.from_user.mention}"
            )

        if action == "resume":
            await AppleVC.resume(assistant, chat_id)
            await query.answer("Music resumed.")
            return await query.message.reply_text(
                f"▶️ Resumed by {query.from_user.mention}"
            )

        if action == "stop":
            await AppleVC.leave(assistant, chat_id)
            await clear_queue(chat_id)
            await query.answer("Music stopped.")
            return await query.message.reply_text(
                f"⏹ Stopped by {query.from_user.mention}"
            )

        if action == "skip":
            await pop_current(chat_id)
            next_track = get_current_track(chat_id)

            if not next_track:
                await AppleVC.leave(assistant, chat_id)
                await clear_queue(chat_id)
                await query.answer("Queue finished.")
                return await query.message.reply_text(
                    "⏹ Queue finished. Left voice chat."
                )

            await AppleVC.change_stream(
                assistant,
                chat_id,
                next_track["path"],
                video=next_track.get("stream_type") == "video",
            )

            await query.answer("Track skipped.")
            return await query.message.reply_text(
                f"⏭ Skipped by {query.from_user.mention}\n\n"
                f"▶️ **Now Playing:** {next_track['title']}"
            )

    except Exception as e:
        return await query.answer(
            f"Error: {str(e)[:150]}",
            show_alert=True,
        )
