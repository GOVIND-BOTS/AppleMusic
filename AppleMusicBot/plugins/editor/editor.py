
import os
import tempfile

from pyrogram import filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import MessageNotModified

from AppleMusicBot import app
from AppleMusicBot.plugins.editor.keyboards import (
    editor_menu,
    music_cancel,
)
from AppleMusicBot.plugins.editor.engine import (
    render_photo,
    render_video,
)

from config import BANNED_USERS


SESSIONS = {}

MAX_INPUT_SIZE = 500 * 1024 * 1024
MAX_AUDIO_SIZE = 100 * 1024 * 1024


def get_session(user_id):
    return SESSIONS.get(user_id)


def cleanup_session(user_id):
    session = SESSIONS.pop(user_id, None)

    if session:
        try:
            session["directory"].cleanup()
        except Exception:
            pass


def make_session(user_id, chat_id):
    cleanup_session(user_id)

    directory = tempfile.TemporaryDirectory(
        prefix=f"applecut_{user_id}_"
    )

    session = {
        "directory": directory,
        "folder": directory.name,
        "media": None,
        "type": None,
        "music": None,
        "effect": "cinematic",
        "duration": 10,
        "start_time": 0,
        "awaiting_music": False,
        "awaiting_start": False,
        "busy": False,
        "chat_id": chat_id,
        "menu_message_id": None,
    }

    SESSIONS[user_id] = session
    return session


async def safe_edit(message, text, reply_markup=None):
    try:
        return await message.edit_text(
            text,
            reply_markup=reply_markup,
        )
    except MessageNotModified:
        return message


def menu_text(session):
    media_type = session["type"]
    duration = session["duration"]

    if media_type == "photo":
        title = "PHOTO TO VIDEO"
        timing = f"📸 Photo video duration: <b>{duration} seconds</b>"
    else:
        title = "VIDEO EDITOR"
        timing = (
            f"🎬 Selected clip length: <b>{duration} seconds</b>\n"
            f"⏱ Start time: <b>{session['start_time']} seconds</b>"
        )

    return (
        "🍎 <b>APPLECUT VIDEO EDITOR</b>\n\n"
        f"✨ <b>{title}</b>\n\n"
        f"🎨 Selected style: <b>{session['effect'].upper()}</b>\n"
        f"{timing}\n\n"
        "🎵 Replace original audio with your music.\n"
        "🎬 Render your project in 4K Ultra HD.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📺 Output: <b>3840 × 2160</b>\n"
        "🎞 FPS: <b>30</b>\n"
        "🎥 Format: <b>MP4</b>\n"
        "━━━━━━━━━━━━━━━━━━"
    )


def make_keyboard(session):
    return editor_menu(
        effect=session["effect"],
        duration=session["duration"],
        media_type=session["type"],
        start_time=session["start_time"],
    )


def valid_session(user_id, message):
    session = get_session(user_id)

    if not session:
        return None

    if session["chat_id"] != message.chat.id:
        return None

    if session["menu_message_id"] != message.id:
        return None

    return session


def parse_time(value):
    """
    Accepts:
    15
    01:15
    00:01:15
    """
    value = value.strip()

    if value.isdigit():
        return int(value)

    parts = value.split(":")

    if not all(part.isdigit() for part in parts):
        raise ValueError("Invalid time format.")

    if len(parts) == 2:
        minutes, seconds = map(int, parts)
        if seconds >= 60:
            raise ValueError("Seconds must be below 60.")
        return minutes * 60 + seconds

    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        if minutes >= 60 or seconds >= 60:
            raise ValueError("Invalid time format.")
        return hours * 3600 + minutes * 60 + seconds

    raise ValueError("Use seconds, MM:SS or HH:MM:SS.")


@app.on_message(
    (filters.photo | filters.video) & ~BANNED_USERS
)
async def applecut_media(client, message: Message):

    if not message.from_user:
        return

    user_id = message.from_user.id
    media = message.photo or message.video

    if not media:
        return

    if media.file_size and media.file_size > MAX_INPUT_SIZE:
        await message.reply_text(
            "❌ Media is too large. Maximum input size is 500 MB."
        )
        return

    session = make_session(user_id, message.chat.id)

    if message.photo:
        session["type"] = "photo"
        session["duration"] = 10
        extension = ".jpg"
    else:
        session["type"] = "video"
        session["duration"] = 30
        extension = ".mp4"

    media_path = os.path.join(
        session["folder"],
        "input" + extension,
    )

    status = await message.reply_text(
        "📥 <b>APPLECUT:</b> Downloading your media..."
    )

    try:
        await message.download(file_name=media_path)

        if not os.path.exists(media_path):
            raise RuntimeError("Media download failed.")

        session["media"] = media_path

        menu = await message.reply_text(
            menu_text(session),
            reply_markup=make_keyboard(session),
        )

        session["menu_message_id"] = menu.id

        try:
            await status.delete()
        except Exception:
            pass

    except Exception as error:
        cleanup_session(user_id)

        try:
            await status.edit_text(
                f"❌ Download failed: {str(error)[:300]}"
            )
        except Exception:
            await message.reply_text(
                f"❌ Download failed: {str(error)[:300]}"
            )


@app.on_callback_query(filters.regex(r"^ac:"))
async def applecut_callbacks(client, query: CallbackQuery):

    if not query.from_user or not query.message:
        await query.answer("Invalid session.", show_alert=True)
        return

    user_id = query.from_user.id
    data = query.data

    session = valid_session(user_id, query.message)

    if not session:
        await query.answer(
            "This is not your editing menu. Send your own media.",
            show_alert=True,
        )
        return

    if session["busy"]:
        await query.answer(
            "Your video is already rendering.",
            show_alert=True,
        )
        return

    # Select effect
    if data.startswith("ac:effect:"):

        effect = data.split(":")[-1]

        session["effect"] = effect

        await query.answer(
            f"{effect.upper()} selected!"
        )

        await safe_edit(
            query.message,
            menu_text(session),
            reply_markup=make_keyboard(session),
        )
        return

    # Select duration
    if data.startswith("ac:duration:"):

        value = data.split(":")[-1]

        if value == "info":
            await query.answer(
                "Choose your preferred duration below."
            )
            return

        try:
            duration = int(value)
        except ValueError:
            await query.answer("Invalid duration.", show_alert=True)
            return

        if duration not in (5, 10, 15, 30, 45, 60):
            await query.answer("Unsupported duration.", show_alert=True)
            return

        session["duration"] = duration

        await query.answer(
            f"Duration set to {duration} seconds."
        )

        await safe_edit(
            query.message,
            menu_text(session),
            reply_markup=make_keyboard(session),
        )
        return

    # Select video start time
    if data == "ac:start":

        if session["type"] != "video":
            await query.answer(
                "Start time is only available for videos.",
                show_alert=True,
            )
            return

        session["awaiting_start"] = True

        await query.answer()

        await query.message.reply_text(
            "⏱ <b>VIDEO START TIME</b>\n\n"
            "Send the starting time in one of these formats:\n\n"
            "• <code>15</code> = 15 seconds\n"
            "• <code>01:15</code> = 1 minute 15 seconds\n"
            "• <code>00:01:15</code> = 1 minute 15 seconds\n\n"
            "The selected clip will start from this point."
        )
        return

    # Replace music
    if data == "ac:music":

        session["awaiting_music"] = True

        await query.answer()

        await safe_edit(
            query.message,
            "🎵 <b>REPLACE MUSIC</b>\n\n"
            "Send an audio file or MP3 in this chat.\n\n"
            "Your original audio will be replaced.",
            reply_markup=music_cancel(),
        )
        return

    # Back
    if data == "ac:back":

        session["awaiting_music"] = False

        await query.answer()

        await safe_edit(
            query.message,
            menu_text(session),
            reply_markup=make_keyboard(session),
        )
        return

    # Cancel
    if data == "ac:cancel":

        cleanup_session(user_id)

        await query.answer("Editing cancelled.")

        await safe_edit(
            query.message,
            "❌ <b>APPLECUT:</b> Editing cancelled.",
        )
        return

    # Render
    if data == "ac:render":

        if not session["media"]:
            await query.answer(
                "Media file is missing. Send it again.",
                show_alert=True,
            )
            return

        session["busy"] = True
        session["awaiting_music"] = False
        session["awaiting_start"] = False

        await query.answer("Rendering started. Please wait...")

        status = None

        try:
            status = await safe_edit(
                query.message,
                "🎬 <b>APPLECUT 4K RENDERING</b>\n\n"
                "⏳ Preparing your project...\n"
                "🎨 Applying selected effects...\n"
                f"⏱ Duration: <b>{session['duration']} seconds</b>\n"
                "📺 Rendering 3840 × 2160...\n\n"
                "Please wait.",
            )

            output = os.path.join(
                session["folder"],
                "AppleCut_4K.mp4",
            )

            if session["type"] == "photo":
                await render_photo(
                    session["media"],
                    output,
                    session["effect"],
                    session["music"],
                    session["duration"],
                )

            elif session["type"] == "video":
                await render_video(
                    session["media"],
                    output,
                    session["effect"],
                    session["music"],
                    session["duration"],
                    session["start_time"],
                )

            else:
                raise ValueError("Unsupported media type.")

            if not os.path.exists(output):
                raise RuntimeError("Output video was not created.")

            if os.path.getsize(output) == 0:
                raise RuntimeError("Rendered video is empty.")

            await safe_edit(
                status,
                "📤 <b>APPLECUT:</b> Uploading your final video...",
            )

            await query.message.reply_video(
                video=output,
                caption=(
                    "🍎 <b>APPLECUT EDITOR</b>\n\n"
                    "✨ Your edited video is ready!\n\n"
                    f"🎨 Effect: <b>{session['effect'].upper()}</b>\n"
                    f"⏱ Duration: <b>{session['duration']} seconds</b>\n"
                    "📺 Quality: <b>4K UHD</b>\n"
                    "🎞 FPS: <b>30</b>\n"
                    "🎬 Format: <b>MP4</b>\n\n"
                    "❤️ Powered by AppleMusic"
                ),
                supports_streaming=True,
            )

            try:
                await status.delete()
            except Exception:
                pass

        except Exception as error:

            error_text = (
                "❌ <b>APPLECUT RENDER FAILED</b>\n\n"
                f"<code>{str(error)[:1200]}</code>\n\n"
                "Please try again with another media file."
            )

            if status:
                try:
                    await safe_edit(status, error_text)
                except Exception:
                    await query.message.reply_text(error_text)
            else:
                await query.message.reply_text(error_text)

        finally:
            cleanup_session(user_id)

        return

    await query.answer("Unknown editor action.", show_alert=True)


@app.on_message(
    filters.text & ~BANNED_USERS
)
async def applecut_start_time(client, message: Message):

    if not message.from_user:
        return

    user_id = message.from_user.id
    session = get_session(user_id)

    if not session:
        return

    if session["chat_id"] != message.chat.id:
        return

    if not session["awaiting_start"]:
        return

    if session["busy"]:
        return

    try:
        start_time = parse_time(message.text)

        if start_time < 0:
            raise ValueError("Start time cannot be negative.")

        session["start_time"] = start_time
        session["awaiting_start"] = False

        await message.reply_text(
            f"✅ Video start time set to <b>{start_time} seconds</b>.\n\n"
            "Press the buttons on your AppleCut editing menu "
            "to continue."
        )

    except ValueError as error:
        await message.reply_text(
            f"❌ {str(error)}\n\n"
            "Example: <code>15</code> or <code>01:15</code>"
        )


@app.on_message(
    (filters.audio | filters.document) & ~BANNED_USERS
)
async def applecut_music(client, message: Message):

    if not message.from_user:
        return

    user_id = message.from_user.id
    session = get_session(user_id)

    if not session:
        return

    if session["chat_id"] != message.chat.id:
        return

    if not session["awaiting_music"] or session["busy"]:
        return

    media = message.audio or message.document

    if not media:
        return

    mime = getattr(media, "mime_type", "") or ""

    if message.document and not mime.startswith("audio/"):
        await message.reply_text(
            "❌ Please send a valid audio file."
        )
        return

    if media.file_size and media.file_size > MAX_AUDIO_SIZE:
        await message.reply_text(
            "❌ Audio must be smaller than 100 MB."
        )
        return

    audio_path = os.path.join(
        session["folder"],
        "replacement_audio.mp3",
    )

    try:
        await message.reply_text(
            "🎵 Downloading replacement music..."
        )

        await message.download(file_name=audio_path)

        if not os.path.exists(audio_path):
            raise RuntimeError("Audio download failed.")

        session["music"] = audio_path
        session["awaiting_music"] = False

        menu = await message.reply_text(
            "✅ <b>Music successfully added!</b>\n\n"
            "Your original audio will be replaced.\n"
            "Choose Render 4K from your editing menu.",
            reply_markup=make_keyboard(session),
        )

        # New menu is now the active menu
        session["menu_message_id"] = menu.id

    except Exception as error:
        await message.reply_text(
            f"❌ Audio download failed: {str(error)[:300]}"
        )
