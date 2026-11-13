
import asyncio
import base64
import os
import re
from pathlib import Path

import yt_dlp
from pyrogram.enums import MessageEntityType


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _seconds(duration):
        try:
            return int(duration or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _duration(seconds):
        seconds = int(seconds or 0)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @staticmethod
    def _cookie_options():
        """Load cookies from file or Base64 environment variable."""
        cookie_file = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()

        if cookie_file and os.path.isfile(cookie_file):
            return {"cookiefile": cookie_file}

        encoded = os.getenv("YOUTUBE_COOKIES_BASE64", "").strip()

        if not encoded:
            return {}

        cookie_path = Path("/tmp/youtube_cookies.txt")

        try:
            cookie_data = base64.b64decode(
                encoded,
                validate=True,
            ).decode("utf-8")

            if not (
                cookie_data.startswith("# Netscape HTTP Cookie File")
                or cookie_data.startswith("# HTTP Cookie File")
            ):
                raise ValueError("Invalid Netscape cookies format.")

            cookie_path.write_text(
                cookie_data,
                encoding="utf-8",
            )
            os.chmod(cookie_path, 0o600)

            return {"cookiefile": str(cookie_path)}

        except Exception as e:
            raise ValueError(
                f"Unable to load YouTube cookies: {e}"
            )

    @classmethod
    def _options(cls, **kwargs):
        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "ignoreerrors": False,
            "retries": 3,
            "fragment_retries": 3,
            "socket_timeout": 30,
        }

        options.update(cls._cookie_options())
        options.update(kwargs)

        return options

    @staticmethod
    def _extract(url, download=False, options=None):
        with yt_dlp.YoutubeDL(options or {}) as ydl:
            return ydl.extract_info(
                url,
                download=download,
            )

    async def exists(self, link, videoid=None):
        if not link:
            return False

        if videoid:
            link = self.base + str(link)

        return bool(
            re.search(self.regex, str(link), re.I)
        )

    async def valid(self, link):
        return await self.exists(link)

    async def url(self, message):
        messages = [
            message,
            message.reply_to_message,
        ]

        for msg in messages:
            if not msg:
                continue

            text = msg.text or msg.caption or ""
            entities = (
                msg.entities
                or msg.caption_entities
                or []
            )

            for entity in entities:
                if entity.type == MessageEntityType.URL:
                    return text[
                        entity.offset:
                        entity.offset + entity.length
                    ]

                if entity.type == MessageEntityType.TEXT_LINK:
                    return entity.url

            match = re.search(
                r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/\S+",
                text,
                re.I,
            )

            if match:
                return match.group(0).rstrip(".,)")

        return None

    async def search(self, query):
        loop = asyncio.get_running_loop()

        def _search():
            info = self._extract(
                f"ytsearch5:{query}",
                options=self._options(
                    extract_flat=True,
                ),
            )

            results = []

            for item in info.get("entries") or []:
                if not item:
                    continue

                video_id = item.get("id")
                if not video_id:
                    continue

                duration = self._seconds(
                    item.get("duration")
                )

                results.append({
                    "title": item.get("title") or "Unknown",
                    "link": self.base + video_id,
                    "duration": self._duration(duration),
                    "duration_sec": duration,
                    "videoid": video_id,
                    "thumbnail": (
                        item.get("thumbnail")
                        or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                    ),
                })

            return results

        return await loop.run_in_executor(
            None,
            _search,
        )

    async def track(self, query, videoid=False):
        if videoid:
            query = self.base + str(query)

        if not await self.exists(query):
            results = await self.search(query)

            if not results:
                raise ValueError("No YouTube results found.")

            query = results[0]["link"]

        loop = asyncio.get_running_loop()

        def _track():
            info = self._extract(
                query,
                options=self._options(),
            )

            vidid = info.get("id")

            if not vidid:
                raise ValueError("YouTube video ID not found.")

            duration_sec = self._seconds(
                info.get("duration")
            )

            details = {
                "title": info.get("title") or "Unknown",
                "link": (
                    info.get("webpage_url")
                    or self.base + vidid
                ),
                "vidid": vidid,
                "videoid": vidid,
                "duration_min": self._duration(duration_sec),
                "duration_sec": duration_sec,
                "thumb": (
                    info.get("thumbnail")
                    or f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg"
                ),
            }

            return details, vidid

        return await loop.run_in_executor(
            None,
            _track,
        )

    async def details(self, link, videoid=False):
        details, vidid = await self.track(
            link,
            videoid,
        )

        return (
            details["title"],
            details["duration_min"],
            details["duration_sec"],
            details["thumb"],
            vidid,
        )

    async def playlist(self, link, limit=25, user_id=None):
        loop = asyncio.get_running_loop()

        def _playlist():
            info = self._extract(
                link,
                options=self._options(
                    noplaylist=False,
                    extract_flat=True,
                ),
            )

            results = []

            for item in info.get("entries") or []:
                if not item:
                    continue

                video_id = item.get("id")

                if video_id:
                    results.append(video_id)

                if len(results) >= int(limit):
                    break

            if not results:
                raise ValueError(
                    "Playlist is empty or unavailable."
                )

            return results

        return await loop.run_in_executor(
            None,
            _playlist,
        )

    async def download(
        self,
        link,
        mystic=None,
        video=False,
        videoid=False,
    ):
        if videoid:
            link = self.base + str(link)

        loop = asyncio.get_running_loop()

        def _download():
            options = self._options(
                outtmpl=str(
                    self.download_dir / "%(id)s.%(ext)s"
                ),
                noplaylist=True,
                continuedl=True,
                nopart=False,
                overwrites=False,
            )

            if video:
                options["format"] = (
                    "best[height<=720][ext=mp4]/"
                    "best[height<=720]/best"
                )
                options["merge_output_format"] = "mp4"

            else:
                options["format"] = "bestaudio/best"
                options["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(
                    link,
                    download=True,
                )

                if not info:
                    raise ValueError(
                        "YouTube download returned no data."
                    )

                video_id = info.get("id")

                if not video_id:
                    raise ValueError(
                        "YouTube video ID missing."
                    )

                if video:
                    path = Path(
                        ydl.prepare_filename(info)
                    )

                    if not path.exists():
                        candidates = list(
                            self.download_dir.glob(
                                f"{video_id}.*"
                            )
                        )
                        candidates = [
                            p for p in candidates
                            if p.suffix.lower() not in (
                                ".part",
                                ".ytdl",
                            )
                        ]

                        if not candidates:
                            raise FileNotFoundError(
                                "Downloaded video file not found."
                            )

                        path = candidates[0]

                else:
                    path = (
                        self.download_dir
                        / f"{video_id}.mp3"
                    )

                if not path.is_file():
                    raise FileNotFoundError(
                        f"Downloaded file missing: {path}"
                    )

                return str(path.resolve())

        file_path = await loop.run_in_executor(
            None,
            _download,
        )

        return file_path, True

    async def video(self, link, videoid=False):
        try:
            if videoid:
                link = self.base + str(link)

            loop = asyncio.get_running_loop()

            def _get_url():
                info = self._extract(
                    link,
                    options=self._options(
                        format="best[height<=720]/best",
                    ),
                )

                return info.get("url")

            stream_url = await loop.run_in_executor(
                None,
                _get_url,
            )

            if stream_url:
                return 1, stream_url

            return 0, "Unable to fetch YouTube stream URL."

        except Exception:
            return 0, "Unable to fetch YouTube stream URL."
