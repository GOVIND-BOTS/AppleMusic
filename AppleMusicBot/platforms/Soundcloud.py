import asyncio
import logging
import os
from pathlib import Path

import yt_dlp


class SoundAPI:
    def __init__(self):
        self.regex = r"^(https?://(?:m\.|www\.)?soundcloud\.com/)(.*)$"
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def valid(self, url: str):
        import re
        return bool(re.search(self.regex, url or "", re.I))

    async def resolve(self, url: str):
        return url

    async def download(self, url: str):
        """Download a SoundCloud track to a local MP3 for voice-chat playback."""
        loop = asyncio.get_running_loop()

        def _download():
            options = {
                "format": "bestaudio/best",
                "outtmpl": str(self.download_dir / "%(id)s.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "retries": 2,
                "fragment_retries": 2,
                "socket_timeout": 25,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise ValueError("SoundCloud returned no track data")
                track_id = str(info.get("id") or "")
                if not track_id:
                    raise ValueError("SoundCloud track ID is missing")

                candidates = list(self.download_dir.glob(f"{track_id}.*"))
                candidates = [
                    path for path in candidates
                    if path.is_file() and path.suffix.lower() not in {".part", ".ytdl"}
                ]
                mp3 = self.download_dir / f"{track_id}.mp3"
                path = mp3 if mp3.is_file() else (
                    candidates[0] if candidates else None
                )
                if not path:
                    raise FileNotFoundError("Downloaded SoundCloud audio file is missing")

                duration = int(info.get("duration") or 0)
                minutes, seconds = divmod(duration, 60)
                details = {
                    "title": info.get("title") or "SoundCloud Track",
                    "duration_sec": duration,
                    "duration_min": f"{minutes}:{seconds:02d}",
                    "filepath": str(path.resolve()),
                    "link": info.get("webpage_url") or url,
                }
                return details, str(path.resolve())

        return await loop.run_in_executor(None, _download)
