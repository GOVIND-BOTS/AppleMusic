
import asyncio
import base64
import os
import re
from typing import Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

try:
    from youtubesearchpython.__future__ import VideosSearch
except Exception:
    VideosSearch = None


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"

    @staticmethod
    def _get_cookie_file():
        """
        Read Base64-encoded Netscape cookies from Railway variables.
        Returns None when cookies are not configured.
        """
        encoded = os.environ.get("YOUTUBE_COOKIES_BASE64", "").strip()

        if not encoded:
            return None

        cookie_path = "/tmp/youtube_cookies.txt"

        try:
            cookie_data = base64.b64decode(
                "".join(encoded.split()),
                validate=True,
            ).decode("utf-8")

            if "Netscape HTTP Cookie File" not in cookie_data:
                raise ValueError("Invalid Netscape cookies format")

            with open(cookie_path, "w", encoding="utf-8") as file:
                file.write(cookie_data)

            os.chmod(cookie_path, 0o600)
            return cookie_path

        except Exception as error:
            raise RuntimeError(
                "YOUTUBE_COOKIES_BASE64 is invalid. "
                "Check that you supplied Base64-encoded Netscape cookies."
            ) from error

    async def exists(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + str(link)

        return bool(re.search(self.regex, link or ""))

    async def url(self, message: Message):
        messages = [message]

        if message.reply_to_message:
            messages.append(message.reply_to_message)

        for msg in messages:
            if not msg:
                continue

            text = msg.text or msg.caption or ""
            entities = msg.entities or msg.caption_entities or []

            for entity in entities:
                if entity.type == MessageEntityType.URL:
                    return text[
                        entity.offset:entity.offset + entity.length
                    ]

                if entity.type == MessageEntityType.TEXT_LINK:
                    return entity.url

        return None

    async def details(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + str(link)

        if not VideosSearch:
            return "Unknown", "0:00", 0, None, link.split("v=")[-1][:11]

        search = VideosSearch(link, limit=1)
        result = (await search.next()).get("result") or []

        if not result:
            return "Unknown", "0:00", 0, None, ""

        track = result[0]
        title = track.get("title", "Unknown")
        duration_min = track.get("duration") or "0:00"
        thumbnail = (track.get("thumbnails") or [{}])[-1].get("url")
        vidid = track.get("id", "")

        seconds = sum(
            int(x) * 60**i
            for i, x in enumerate(
                reversed(str(duration_min).split(":"))
            )
        )

        return title, duration_min, seconds, thumbnail, vidid

    async def search(self, query: str):
        if not VideosSearch:
            return []

        search = VideosSearch(query, limit=5)
        result = (await search.next()).get("result") or []

        tracks = []

        for item in result:
            duration = item.get("duration") or "0:00"

            tracks.append(
                {
                    "title": item.get("title", "Unknown"),
                    "link": item.get("link"),
                    "duration": duration,
                    "videoid": item.get("id"),
                    "thumbnail": (
                        item.get("thumbnails") or [{}]
                    )[-1].get("url"),
                }
            )

        return tracks

    async def video(
        self,
        link: str,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + str(link)

        try:
            command = [
                "yt-dlp",
                "-g",
                "-f",
                "best[height<=?720][width<=?1280]",
            ]

            cookie_file = self._get_cookie_file()

            if cookie_file:
                command.extend(["--cookies", cookie_file])

            command.append(link)

            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await proc.communicate()

            if proc.returncode == 0 and stdout:
                stream_url = stdout.decode().strip().split("\n")[0]
                if stream_url:
                    return 1, stream_url

            return 0, "Unable to fetch stream URL"

        except Exception:
            return 0, "Unable to fetch stream URL"

    async def track(self, query: str):
        tracks = await self.search(query)

        if not tracks:
            return None

        track = tracks[0]

        return {
            "title": track["title"],
            "link": track["link"],
            "duration": track["duration"],
            "videoid": track["videoid"],
            "thumbnail": track["thumbnail"],
        }

    async def download(
        self,
        link: str,
        video: bool = False,
        videoid: Union[bool, str] = None,
    ):
        if videoid:
            link = self.base + str(link)

        os.makedirs("downloads", exist_ok=True)

        ydl_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        cookie_file = self._get_cookie_file()

        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        if video:
            ydl_opts["format"] = "best[height<=?720][width<=?1280]"
        else:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

        loop = asyncio.get_running_loop()

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)

                if video:
                    return ydl.prepare_filename(info)

                return os.path.join(
                    "downloads",
                    f"{info['id']}.mp3",
                )

        path = await loop.run_in_executor(None, _download)
        return path
