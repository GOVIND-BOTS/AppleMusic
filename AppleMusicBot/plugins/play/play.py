import random
import string

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from AppleMusicBot import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app
from AppleMusicBot.core.call import AppleBot
from AppleMusicBot.logging import LOGGER
from AppleMusicBot.utils import seconds_to_min, time_to_seconds
from AppleMusicBot.utils.channelplay import get_channeplayCB
from AppleMusicBot.utils.decorators.language import languageCB
from AppleMusicBot.utils.decorators.play import PlayWrapper
from AppleMusicBot.utils.formatters import formats
from AppleMusicBot.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from AppleMusicBot.utils.logger import play_logs
from AppleMusicBot.utils.stream.stream import stream
from config import BANNED_USERS, lyrical


@app.on_message(
    filters.command(
        ["play", "vplay", "cplay", "cvplay", "playforce", "vplayforce", "cplayforce", "cvplayforce"]
    )
    & filters.group
    & ~BANNED_USERS,
    group=10,
)
@PlayWrapper
async def play_commnd(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    LOGGER(__name__).info(
        f"PLAY HANDLER STARTED | User: {message.from_user.id if message.from_user else None} | "
        f"Chat: {message.chat.id} | Text: {message.text}"
    )

    try:
        mystic = await message.reply_text(
            _["play_2"].format(channel) if channel else _["play_1"]
        )
    except Exception as e:
        LOGGER(__name__).error(f"Failed to send initial play message: {e}")
        return

    plist_id = None
    slider = None
    plist_type = None
    spotify = None
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )

    if audio_telegram or video_telegram:
        media = audio_telegram or video_telegram
        is_video = bool(video_telegram)
        size = getattr(media, "file_size", 0) or 0
        limit = (
            config.TG_VIDEO_FILESIZE_LIMIT
            if is_video
            else config.TG_AUDIO_FILESIZE_LIMIT
        )
        if size > limit:
            return await mystic.edit_text(
                _["play_8"] if is_video else _["play_5"]
            )

        duration = getattr(media, "duration", 0) or 0
        if duration and duration > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )

        if is_video and message.reply_to_message.document:
            filename = getattr(media, "file_name", "") or ""
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext not in formats:
                return await mystic.edit_text(
                    _["play_7"].format(f"{' | '.join(formats)}")
                )

        try:
            downloaded = await Telegram.download(message, video=is_video)
        except Exception as exc:
            LOGGER(__name__).exception("Telegram media download failed: %s", exc)
            return await mystic.edit_text(
                "❌ Telegram media download failed. Please try another file."
            )

        if not downloaded or not downloaded.get("path"):
            return await mystic.edit_text(
                "❌ Unable to download this Telegram media. Check file size and try again."
            )

        try:
            reply = message.reply_to_message
            message_link = getattr(reply, "link", None) if reply else None
            message_link = message_link or config.SUPPORT_CHAT
            file_duration = seconds_to_min(downloaded.get("duration", 0))
            details = {
                "title": downloaded["title"],
                "link": message_link,
                "path": downloaded["path"],
                "dur": file_duration,
            }
            await stream(
                _, mystic, user_id, details, chat_id, user_name,
                message.chat.id, video=is_video,
                streamtype="telegram", forceplay=fplay,
            )
        except Exception as exc:
            LOGGER(__name__).exception("Telegram media playback failed: %s", exc)
            ex_type = type(exc).__name__
            err = exc if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
            return await mystic.edit_text(err)
        return await mystic.delete()

    elif url:
        if await YouTube.exists(url):
            if "playlist" in url:
                try:
                    details = await YouTube.playlist(
                        url, config.PLAYLIST_FETCH_LIMIT, message.from_user.id
                    )
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "yt"
                if "&" in url:
                    plist_id = (url.split("=")[1]).split("&")[0]
                else:
                    plist_id = url.split("=")[1]
                img = config.PLAYLIST_IMG_URL
                cap = _["play_9"]
            else:
                try:
                    details, track_id = await YouTube.track(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_10"].format(details["title"], details["duration_min"])
        elif await Spotify.valid(url):
            # Spotify supplies catalogue metadata; the actual playable stream is
            # resolved through the configured YouTube extractor.
            if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
                return await mystic.edit_text(
                    "» Spotify link playback needs SPOTIFY_CLIENT_ID and "
                    "SPOTIFY_CLIENT_SECRET in the bot environment."
                )
            if "track" in url:
                try:
                    metadata = await Spotify.track(url)
                    if not metadata or not metadata.get("query"):
                        raise ValueError("Spotify track metadata unavailable")
                    details, track_id = await YouTube.track(metadata["query"])
                except Exception as exc:
                    LOGGER(__name__).exception("Spotify track resolution failed: %s", exc)
                    return await mystic.edit_text(_["play_3"])
                streamtype = "youtube"
                img = details["thumb"]
                cap = _["play_10"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spplay"
                img = config.SPOTIFY_PLAYLIST_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spalbum"
                img = config.SPOTIFY_ALBUM_IMG_URL
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spartist"
                img = config.SPOTIFY_ARTIST_IMG_URL
                cap = _["play_11"].format(message.from_user.first_name)
            else:
                return await mystic.edit_text(_["play_15"])
        elif await Apple.valid(url):
            # Apple Music page metadata is resolved to a playable audio source.
            try:
                metadata = await Apple.track(url)
                query = (metadata or {}).get("query") or (metadata or {}).get("title")
                if not query or query == "Apple Music Track":
                    raise ValueError("Apple Music did not expose track metadata")
                details, track_id = await YouTube.track(query)
            except Exception as exc:
                LOGGER(__name__).exception("Apple Music track resolution failed: %s", exc)
                return await mystic.edit_text(_["play_3"])
            streamtype = "youtube"
            img = details["thumb"]
            cap = _["play_10"].format(details["title"], details["duration_min"])
        elif await Resso.valid(url):
            try:
                metadata = await Resso.track(url)
                query = (metadata or {}).get("query") or (metadata or {}).get("title")
                if not query or query == "Resso Track":
                    raise ValueError("Resso did not expose track metadata")
                details, track_id = await YouTube.track(query)
            except Exception as exc:
                LOGGER(__name__).exception("Resso track resolution failed: %s", exc)
                return await mystic.edit_text(_["play_3"])
            streamtype = "youtube"
            img = details["thumb"]
            cap = _["play_10"].format(details["title"], details["duration_min"])
        elif await SoundCloud.valid(url):
            try:
                details, track_path = await SoundCloud.download(url)
            except:
                return await mystic.edit_text(_["play_3"])
            duration_sec = details["duration_sec"]
            if duration_sec > config.DURATION_LIMIT:
                return await mystic.edit_text(
                    _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
                )
            try:
                await stream(
                    _, mystic, user_id, details, chat_id, user_name,
                    message.chat.id, streamtype="soundcloud", forceplay=fplay,
                )
            except Exception as e:
                LOGGER(__name__).exception(
                    "Direct playback failed | streamtype=%s | chat_id=%s",
                    streamtype, chat_id,
                )
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        else:
            try:
                await AppleBot.stream_call(url)
            except NoActiveGroupCall:
                await mystic.edit_text(_["black_9"])
                return
            except Exception as e:
                return await mystic.edit_text(_["general_2"].format(type(e).__name__))
            await mystic.edit_text(_["str_2"])
            try:
                await stream(
                    _, mystic, message.from_user.id, url, chat_id,
                    message.from_user.first_name, message.chat.id,
                    video=video, streamtype="index", forceplay=fplay,
                )
            except Exception as e:
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await play_logs(message, streamtype="M3u8 or Index Link")
    else:
        if len(message.command) < 2:
            buttons = botplaylist_markup(_)
            return await mystic.edit_text(
                _["play_18"],
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        slider = True
        query = message.text.split(None, 1)[1]
        if "-v" in query:
            query = query.replace("-v", "")
        try:
            details, track_id = await YouTube.track(query)
        except Exception as e:
            LOGGER(__name__).error(f"YouTube track search failed: {e}")
            return await mystic.edit_text(_["play_3"])
        streamtype = "youtube"

    # Direct play mode
    if str(playmode) == "Direct":
        if not plist_type:
            if details.get("duration_min"):
                duration_sec = time_to_seconds(details["duration_min"])
                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(
                        _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
                    )
            try:
                await stream(
                    _, mystic, user_id, details, chat_id, user_name,
                    message.chat.id, video=video, streamtype=streamtype, forceplay=fplay,
                )
            except Exception as e:
                LOGGER(__name__).exception(
                    "SoundCloud playback failed | chat_id=%s", chat_id
                )
                ex_type = type(e).__name__
                err = e if ex_type == "AssistantErr" else _["general_2"].format(ex_type)
                return await mystic.edit_text(err)
            return await mystic.delete()
        else:
            # Playlist handling (simplified for now)
            return await mystic.edit_text("Playlist support is loading...")
    else:
        # Inline mode (slider)
        buttons = track_markup(_, track_id, message.from_user.id)
        return await mystic.edit_text(
            cap,
            reply_markup=InlineKeyboardMarkup(buttons),
        )
