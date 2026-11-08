
from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app, userbot
from AppleMusicBot.core.call import Apple as AppleVC
from AppleMusicBot.utils.decorators.admins import AdminRightsCheck
from AppleMusicBot.utils.stream.queue import (
    clear_queue,
    get_current_track,
    pop_current,
)
from config import BANNED_USERS


@app.on_message(
    filters.command(["skip", "cskip", "next"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def skip_cmd(_, message: Message):
    chat_id = message.chat.id

    if not userbot.assistants:
        return await message.reply_text(
            "❌ No assistant is available."
        )

    assistant = userbot.assistants[0]
    status = await message.reply_text("⏭ **Skipping current track...**")

    try:
        await pop_current(chat_id)
        next_track = get_current_track(chat_id)

        if not next_track:
            await AppleVC.leave(assistant, chat_id)
            await clear_queue(chat_id)

            return await status.edit_text(
                "⏹ **Queue finished.**\n"
                "Left the voice chat."
            )

        await AppleVC.change_stream(
            assistant,
            chat_id,
            next_track["path"],
            video=next_track.get("stream_type") == "video",
        )

        name = (
            message.from_user.mention
            if message.from_user
            else "Admin"
        )

        await status.edit_text(
            f"⏭ **Skipped by:** {name}\n\n"
            f"▶️ **Now Playing:** {next_track['title']}"
        )

    except Exception as e:
        await AppleVC.leave(assistant, chat_id)
        await clear_queue(chat_id)

        await status.edit_text(
            f"❌ **Skip failed.**\n\n`{e}`"
        )
