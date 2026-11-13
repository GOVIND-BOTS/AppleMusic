
import os
import tempfile
import shutil
import asyncio

from pyrogram import filters
from pyrogram.types import Message, CallbackQuery

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


# Per-user editing sessions.
SESSIONS = {}

MAX_INPUT_SIZE = 500 * 1024 * 1024


def get_session(user_id):
    return SESSIONS.get(user_id)


def cleanup_session(user_id):
    session = SESSIONS.pop(user_id, None)

    if session:
        try:
            session["directory"].cleanup()
        except Exception:
            pass


def make_session(user_id):
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
    }

    SESSIONS[user_id] = session
    return session


def menu_text():
    return (
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


@app.on_message(
    (filters.photo | filters.video) & ~BANNED_USERS
)
async def applecut_media(client, message: Message):
    user_id = message.from_user.id

    media = message.photo or message.video

    if not media:
        return

    if media.file_size and media.file_size > MAX_INPUT_SIZE:
        await message.reply_text(
            "❌ Media is too large. Maximum input size is 500 MB."
        )
        return

    session = make_session(user_id)

    extension = (
        ".jpg" if message.photo else ".mp4"
    )

    media_path = os.path.join(
        session["folder"],
        "input" + extension,
    )

    try:
        await message.reply_text(
            "📥 <b>APPLECUT:</b> Downloading your media..."
        )

        await message.download(
            file_name=media_path
        )

        session["media"] = media_path
        session["type"] = (
            "photo" if message.photo else "video"
        )

        await message.reply_text(
            menu_text(),
            reply_markup=editor_menu(),
        )

    except Exception as error:
        cleanup_session(user_id)

        await message.reply_text(
            f"❌ Download failed: {str(error)[:300]}"
        )


@app.on_callback_query(
    filters.regex(r"^ac:")
)
async def applecut_callbacks(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    session = get_session(user_id)

    if not session:
        await query.answer(
            "Please send a new photo or video.",
            show_alert=True,
        )
        return

    if session["busy"]:
        await query.answer(
            "Your video is already rendering.",
            show_alert=True,
        )
        return

    if data.startswith("ac:effect:"):
        effect = data.split(":")[-1]

        session["effect"] = effect

        await query.answer(
            f"{effect.upper()} effect selected!"
        )

        await query.message.edit_text(
            menu_text()
            + f"\n\n🎨 Selected effect: <b>{effect.upper()}</b>",
            reply_markup=editor_menu(effect),
        )
        return

    if data == "ac:music":
        session["awaiting_music"] = True

        await query.answer()

        await query.message.edit_text(
            "🎵 <b>REPLACE MUSIC</b>\n\n"
            "Now send an audio file or MP3.\n\n"
            "The original audio will be replaced "
            "with your uploaded music.",
            reply_markup=music_cancel(),
        )
        return

    if data == "ac:back":
        session["awaiting_music"] = False

        await query.answer()

        await query.message.edit_text(
            menu_text(),
            reply_markup=editor_menu(session["effect"]),
        )
        return

    if data == "ac:cancel":
        cleanup_session(user_id)

        await query.answer("Editing cancelled.")

        await query.message.edit_text(
            "❌ <b>APPLECUT:</b> Editing cancelled."
        )
        return

    if data == "ac:render":
        await query.answer(
            "Rendering started. Please wait..."
        )

        session["busy"] = True

        status = await query.message.edit_text(
            "🎬 <b>APPLECUT 4K RENDERING</b>\n\n"
            "⏳ Preparing your video...\n"
            "🎨 Applying effects...\n"
            "📺 Rendering 3840 × 2160..."
        )

        output = os.path.join(
            session["folder"],
            "AppleCut_4K.mp4",
        )

        try:
            if not session["media"]:
                raise ValueError("Media file is missing.")

            if session["type"] == "photo":
                await render_photo(
                    session["media"],
                    output,
                    session["effect"],
                    session["music"],
                )
            else:
                await render_video(
                    session["media"],
                    output,
                    session["effect"],
                    session["music"],
                )

            if not os.path.exists(output):
                raise RuntimeError("Output video was not created.")

            size = os.path.getsize(output)

            if size == 0:
                raise RuntimeError("Rendered video is empty.")

            await status.edit_text(
                "📤 <b>APPLECUT:</b> Uploading your final video..."
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

            await status.delete()

        except Exception as error:
            await status.edit_text(
                "❌ <b>APPLECUT RENDER FAILED</b>\n\n"
                f"<code>{str(error)[:1500]}</code>\n\n"
                "Please try again with another media file."
            )

        finally:
            cleanup_session(user_id)

        return


@app.on_message(
    (filters.audio | filters.document) & ~BANNED_USERS
)
async def applecut_music(client, message: Message):
    user_id = message.from_user.id
    session = get_session(user_id)

    if not session or not session["awaiting_music"]:
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

    if media.file_size and media.file_size > 100 * 1024 * 1024:
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
