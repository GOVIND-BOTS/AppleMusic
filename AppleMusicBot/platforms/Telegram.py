import os

from pyrogram.types import Message

import config


class TelegramAPI:
    def __init__(self):
        self.chars_limit = 4096
        self.dl_dir = "downloads"

    async def download(self, message: Message, video: bool = False):
        """Download media attached to, or replied to by, a play command."""
        source = message
        media = (
            source.audio or source.voice or source.video or source.document
        )
        if not media and message.reply_to_message:
            source = message.reply_to_message
            media = source.audio or source.voice or source.video or source.document
        if not media:
            return None

        is_video = bool(video or source.video)
        size = getattr(media, "file_size", 0) or 0
        limit = (
            config.TG_VIDEO_FILESIZE_LIMIT
            if is_video
            else config.TG_AUDIO_FILESIZE_LIMIT
        )
        if size > limit:
            return None

        os.makedirs(self.dl_dir, exist_ok=True)
        path = await source.download(file_name=f"{self.dl_dir}/")
        if not path or not os.path.isfile(path):
            return None

        title = (
            getattr(media, "title", None)
            or getattr(media, "file_name", None)
            or "Telegram Media"
        )
        duration = getattr(media, "duration", 0) or 0
        return {
            "path": path,
            "title": title,
            "duration": int(duration),
            "is_video": is_video,
        }
