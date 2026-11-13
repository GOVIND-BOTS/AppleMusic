
import os
import tempfile
import asyncio

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


# Per-user editing sessions
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
        "awaiting_music": False,
        "busy": False,
        "chat_id": chat_id,
        "menu_message_id": None,
    }

    SESSIONS[user_id] = session
    return session


async def safe_edit(message, text, reply_markup=None):
    """
    Avoid MESSAGE_NOT_MODIFIED errors.
    """
    try:
        return await message.edit_text(
            text,
            reply_markup=reply_markup,
        )
    except MessageNotModified:
        return message
    except Exception:
        raise


def menu_text(effect=None):
    text = (
        "🍎 <b>APPLECUT VIDEO EDITOR</b>\n\n"
        "Your media is ready for editing!\n\n"
        "✨ Choose your favourite effect below.\n"
        "🎵 Replace the original audio with your music.\n"
        "🎬 Render your project in 4K Ultra HD.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📺 Output: <b>3840 × 2160</b>\n"
        "🎞 FPS: <b>30</b>\n"
        "🎥 Format: <b>MP4</b>\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    if effect:
        text += (
            f"\n\n🎨 Selected effect: "
            f"<b>{effect.upper()}</b>"
        )

    return text


def valid_session(user_id, message):
    session = get_session(user_id)

    if not session:
        return None

    if session["chat_id"] != message.chat.id:
        return None

    if session["menu_message_id"] != message.id:
        return None

    return session


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

    session = make_session(
        user_id,
        message.chat.id,
    )

    extension = ".jpg" if message.photo else ".mp4"

    media_path = os.path.join(
        session["folder"],
        "input" + extension,
    )

    status = None

    try:
        status = await message.reply_text(
            "📥 <b>APPLECUT:</b> Downloading your media..."
        )

        await message.download(
            file_name=media_path
        )

        if not os.path.exists(media_path):
            raise RuntimeError("Media download failed.")

        session["media"] = media_path
        session["type"] = (
            "photo" if message.photo else "video"
        )

        menu = await message.reply_text(
            menu_text(session["effect"]),
            reply_markup=editor_menu(session["effect"]),
        )

        session["menu_message_id"] = menu.id

        if status:
            try:
                await status.delete()
            except Exception:
                pass

    except Exception as error:
        cleanup_session(user_id)

        error_text = (
            f"❌ Download failed: {str(error)[:300]}"
        )

        if status:
            try:
                await status.edit_text(error_text)
            except Exception:
                await message.reply_text(error_text)
        else:
            await message.reply_text(error_text)


@app.on_callback_query(
    filters.regex(r"^ac:")
)
async def applecut_callbacks(client, query: CallbackQuery):

    if not query.from_user or not query.message:
        await query.answer(
            "Invalid editing session.",
            show_alert=True,
        )
        return

    user_id = query.from_user.id
    data = query.data

    session = valid_session(
        user_id,
        query.message,
    )

    if not session:
        await query.answer(
            "This is not your editing menu. Send your own photo or video.",
            show_alert=True,
        )
        return

    if session["busy"]:
        await query.answer(
            "Your video is already rendering.",
            show_alert=True,
        )
        return

    # Effect selection
    if data.startswith("ac:effect:"):

        effect = data.split(":")[-1]

        session["effect"] = effect

        await query.answer(
            f"{effect.upper()} effect selected!"
        )

        await safe_edit(
            query.message,
            menu_text(effect),
            reply_markup=editor_menu(effect),
        )
        return

    # Replace music
    if data == "ac:music":

        session["awaiting_music"] = True

        await query.answer()

        await safe_edit(
            query.message,
            "🎵 <b>REPLACE MUSIC</b>\n\n"
            "Now send an audio file or MP3 in this chat.\n\n"
            "The original audio will be replaced "
            "with your uploaded music.",
            reply_markup=music_cancel(),
        )
        return

    # Back to editor menu
    if data == "ac:back":

        session["awaiting_music"] = False

        await query.answer()

        await safe_edit(
            query.message,
            menu_text(session["effect"]),
            reply_markup=editor_menu(session["effect"]),
        )
        return

    # Cancel editing
    if data == "ac:cancel":

        cleanup_session(user_id)

        await query.answer("Editing cancelled.")

        await safe_edit(
            query.message,
            "❌ <b>APPLECUT:</b> Editing cancelled.",
        )
        return

    # Render video
    if data == "ac:render":

        if not session["media"]:
            await query.answer(
                "Media file is missing. Send it again.",
                show_alert=True,
            )
            return

        session["busy"] = True

        await query.answer(
            "Rendering started. Please wait..."
        )

        status = None

        try:
            status = await safe_edit(
                query.message,
                "🎬 <b>APPLECUT 4K RENDERING</b>\n\n"
                "⏳ Preparing your video...\n"
                "🎨 Applying effects...\n"
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
                )

            elif session["type"] == "video":
                await render_video(
                    session["media"],
                    output,
                    session["effect"],
                    session["music"],
                )

            else:
                raise ValueError("Unsupported media type.")

            if not os.path.exists(output):
                raise RuntimeError(
                    "Output video was not created."
                )

            if os.path.getsize(output) == 0:
                raise RuntimeError(
                    "Rendered video is empty."
                )

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

    await query.answer(
        "Unknown editor action.",
        show_alert=True,
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

    if not session["awaiting_music"]:
        return

    if session["busy"]:
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

        await message.download(
            file_name=audio_path
        )

        if not os.path.exists(audio_path):
            raise RuntimeError("Audio download failed.")

        session["music"] = audio_path
        session["awaiting_music"] = False

        await message.reply_text(
            "✅ <b>Music successfully added!</b>\n\n"
            "Your original audio will be replaced.\n"
            "Return to your editing menu and press Render 4K.",
            reply_markup=editor_menu(session["effect"]),
        )

    except Exception as error:
        await message.reply_text(
            f"❌ Audio download failed: {str(error)[:300]}"
        )
