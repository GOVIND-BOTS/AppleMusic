import asyncio
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

    async def exists(self, link: str, videoid: Union[bool, str] = None):
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
                    return text[entity.offset : entity.offset + entity.length]
                if entity.type == MessageEntityType.TEXT_LINK:
                    return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
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
            for i, x in enumerate(reversed(str(duration_min).split(":")))
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
                    "thumbnail": (item.get("thumbnails") or [{}])[-1].get("url"),
                }
            )
        return tracks

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        return 0, "Unable to fetch stream URL"

    async def track(self, query: str):
        tracks = await self.search(query)
        if not tracks:
            return None
        t = tracks[0]
        return {
            "title": t["title"],
            "link": t["link"],
            "duration": t["duration"],
            "videoid": t["videoid"],
            "thumbnail": t["thumbnail"],
        }

    async def download(self, link: str, video: bool = False, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + str(link)
        os.makedirs("downloads", exist_ok=True)
        ydl_opts = {
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }
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

        def _dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                if video:
                    return ydl.prepare_filename(info)
                return os.path.join("downloads", f"{info['id']}.mp3")

        path = await loop.run_in_executor(None, _dl)
        return path
