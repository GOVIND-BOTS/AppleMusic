import os

from pyrogram.types import Message

import config


class TelegramAPI:
    def __init__(self):
        self.chars_limit = 4096
        self.dl_dir = "downloads"

    async def download(self, message: Message, video: bool = False):
        media = message.audio or message.voice or message.video or message.document
        if not media:
            if message.reply_to_message:
                r = message.reply_to_message
                media = r.audio or r.voice or r.video or r.document
        if not media:
            return None

        size = getattr(media, "file_size", 0) or 0
        limit = (
            config.TG_VIDEO_FILESIZE_LIMIT
            if video or message.video
            else config.TG_AUDIO_FILESIZE_LIMIT
        )
        if size > limit:
            return None

        os.makedirs(self.dl_dir, exist_ok=True)
        path = await message.download(file_name=f"{self.dl_dir}/")
        if not path and message.reply_to_message:
            path = await message.reply_to_message.download(
                file_name=f"{self.dl_dir}/"
            )
        title = (
            getattr(media, "title", None)
            or getattr(media, "file_name", None)
            or "Telegram Media"
        )
        duration = getattr(media, "duration", 0) or 0
        return {
            "path": path,
            "title": title,
            "duration": duration,
        }
