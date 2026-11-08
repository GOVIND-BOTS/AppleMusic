import re

from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config
from AppleMusicBot import (
    Apple,
    Resso,
    SoundCloud,
    Spotify,
    Telegram,
    YouTube,
    app,
    userbot,
)
from AppleMusicBot.core.call import Apple as AppleVC
from AppleMusicBot.misc import db
from AppleMusicBot.utils.decorators.play import PlayWrapper
from AppleMusicBot.utils.stream.queue import put_queue
from config import BANNED_USERS


def control_markup():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏸ Pause", callback_data="am_pause"),
                InlineKeyboardButton("▶️ Resume", callback_data="am_resume"),
            ],
            [
                InlineKeyboardButton("⏭ Skip", callback_data="am_skip"),
                InlineKeyboardButton("⏹ Stop", callback_data="am_stop"),
            ],
        ]
    )


async def resolve_query(message: Message, text: str):
    """Detect platform and resolve to a playable youtube query / path."""
    text = (text or "").strip()

    # Telegram audio / video / reply media
    if message.audio or message.voice or message.video or message.document:
        return "telegram", await Telegram.download(message), None
    if message.reply_to_message and (
        message.reply_to_message.audio
        or message.reply_to_message.voice
        or message.reply_to_message.video
        or message.reply_to_message.document
    ):
        return "telegram", await Telegram.download(message), None

    if not text:
        return None, None, None

    # Spotify
    if await Spotify.valid(text):
        data = await Spotify.track(text)
        if data:
            return "spotify", data["query"], data
        return None, None, None

    # Apple Music
    if await Apple.valid(text):
        data = await Apple.track(text)
        if data:
            return "apple", data["query"], data
        return None, None, None

    # Resso
    if await Resso.valid(text):
        data = await Resso.track(text)
        if data:
            return "resso", data["query"], data
        return None, None, None

    # SoundCloud (yt-dlp direct)
    if await SoundCloud.valid(text):
        return "soundcloud", text, {"title": "SoundCloud Track", "link": text}

    # YouTube link or plain search
    if await YouTube.exists(text):
        details = await YouTube.details(text)
        title, duration_min, seconds, thumb, vidid = details
        return (
            "youtube",
            text,
            {
                "title": title,
                "duration": duration_min,
                "seconds": seconds,
                "thumbnail": thumb,
                "videoid": vidid,
                "link": text,
            },
        )

    track = await YouTube.track(text)
    if not track:
        return None, None, None
    return "youtube", track["link"], track


async def play_track(message: Message, video: bool = False):
    chat_id = message.chat.id
    user = message.from_user.mention if message.from_user else "User"

    text = ""
    if message.command and len(message.command) > 1:
        text = message.text.split(None, 1)[1]
    elif message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text

    status = await message.reply_text("🔍 **Searching...**")

    platform, payload, meta = await resolve_query(message, text)
    if not platform or not payload:
        return await status.edit_text(
            "Kuch nahi mila.\n"
            "Try: `/play song name` ya Spotify/Apple/YouTube link."
        )

    assistant = userbot.assistants[0]

    try:
        if platform == "telegram":
            if not payload or not payload.get("path"):
                return await status.edit_text("Telegram media download fail.")
            path = payload["path"]
            title = payload.get("title", "Telegram Media")
            duration = str(payload.get("duration") or 0)
            videoid = ""
            thumb = config.TELEGRAM_AUDIO_URL
        elif platform == "soundcloud":
            path = await YouTube.download(payload, video=video)
            title = (meta or {}).get("title", "SoundCloud")
            duration = "0:00"
            videoid = ""
            thumb = config.SOUNCLOUD_IMG_URL
        else:
            # youtube / spotify / apple / resso → youtube download
            if platform in ("spotify", "apple", "resso"):
                track = await YouTube.track(payload)
                if not track:
                    return await status.edit_text("YouTube pe track nahi mila.")
                link = track["link"]
                title = track["title"]
                duration = track.get("duration", "0:00")
                videoid = track.get("videoid", "")
                thumb = track.get("thumbnail") or config.YOUTUBE_IMG_URL
            else:
                link = payload
                title = (meta or {}).get("title", "Track")
                duration = (meta or {}).get("duration", "0:00")
                videoid = (meta or {}).get("videoid", "")
                thumb = (meta or {}).get("thumbnail") or config.YOUTUBE_IMG_URL

            await status.edit_text("⬇️ **Downloading...**")
            path = await YouTube.download(link, video=video, videoid=False)
    except Exception as e:
        return await status.edit_text(f"Download failed:\n`{e}`")

    pos = await put_queue(
        chat_id,
        title=title,
        duration=str(duration),
        path=path,
        user=user,
        stream_type="video" if video else "audio",
        videoid=videoid or "",
    )

    try:
        if pos == 0:
            await status.edit_text("🎙 **Joining voice chat...**")
            await AppleVC.join(assistant, chat_id, path, video=video)
            caption = (
                f"**▶ Now Playing**\n\n"
                f"**Track:** {title}\n"
                f"**Duration:** `{duration}`\n"
                f"**Platform:** `{platform}`\n"
                f"**Requested by:** {user}\n\n"
                f"🍎 **{config.BOT_NAME}**"
            )
            await status.delete()
            await message.reply_photo(
                photo=thumb or config.YOUTUBE_IMG_URL,
                caption=caption,
                reply_markup=control_markup(),
            )
        else:
            await status.edit_text(
                f"**Queued #{pos + 1}**\n\n"
                f"**Track:** {title}\n"
                f"**Duration:** `{duration}`\n"
                f"**Requested by:** {user}"
            )
    except Exception as e:
        if chat_id in db and db[chat_id]:
            db[chat_id].pop()
        return await status.edit_text(
            f"Voice chat join failed.\n"
            f"Active VC start karo aur bot + assistant ko add karo.\n\n`{e}`"
        )


@app.on_message(
    filters.command(["play", "vplay", "playforce"]) & filters.group & ~BANNED_USERS
)
@PlayWrapper
async def play_command(_, message: Message):
    video = message.command[0].lower().startswith("v")
    await play_track(message, video=video)
