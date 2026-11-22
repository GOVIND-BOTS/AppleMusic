import asyncio
import base64
import logging
import binascii
import os
import re
import shutil
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
    def _validate_cookie_text(data):
        """Validate an exported Netscape cookies.txt without logging its contents."""
        data = (data or "").lstrip("\ufeff").strip()
        first_lines = [line.strip() for line in data.splitlines() if line.strip()]
        has_header = any(
            line in ("# Netscape HTTP Cookie File", "# HTTP Cookie File")
            for line in first_lines[:5]
        )
        if not has_header:
            raise ValueError(
                "Cookies are not in Netscape cookies.txt format. "
                "Export using Firefox's Get cookies.txt extension."
            )
        # Netscape rows contain seven tab-separated columns. Ignore comments.
        cookie_rows = [
            line for line in data.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not cookie_rows or not any(len(row.split("\t")) >= 7 for row in cookie_rows):
            raise ValueError("Netscape cookies file contains no valid cookie rows.")
        return data + "\n"

    @classmethod
    def _write_cookie_data(cls, data, destination):
        cookie_data = cls._validate_cookie_text(data)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(cookie_data, encoding="utf-8")
        try:
            os.chmod(destination, 0o600)
        except OSError:
            pass
        return {"cookiefile": str(destination.resolve())}

    @classmethod
    def _cookie_options(cls):
        """Resolve YouTube cookies from a file or Railway environment variable.

        Supported variables:
          YOUTUBE_COOKIES_FILE   Path to a Netscape cookies.txt file
          YOUTUBE_COOKIES        Raw Netscape cookies text (multiline)
          YOUTUBE_COOKIES_BASE64 Base64-encoded Netscape cookies text
        """
        project_root = Path(__file__).resolve().parents[2]
        default_path = project_root / "cookies.txt"

        # Explicit file path has priority and avoids copying secrets into the repo.
        configured_path = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()
        if configured_path:
            path = Path(configured_path).expanduser()
            if not path.is_file():
                raise ValueError(
                    f"YOUTUBE_COOKIES_FILE points to a missing file: {path}"
                )
            if path.stat().st_size == 0:
                raise ValueError("YOUTUBE_COOKIES_FILE is empty.")
            cls._validate_cookie_text(path.read_text(encoding="utf-8"))
            return {"cookiefile": str(path.resolve())}

        # Plain text variable is convenient for Railway multiline variables.
        raw_cookies = os.getenv("YOUTUBE_COOKIES", "")
        if raw_cookies.strip():
            return cls._write_cookie_data(
                raw_cookies, project_root / "runtime_cookies.txt"
            )

        # Backward compatible: accept Base64, but also detect raw text pasted
        # into this variable (the cause of 'Non-base64 digit found').
        encoded = os.getenv("YOUTUBE_COOKIES_BASE64", "").strip()
        if encoded:
            decoded = None
            try:
                decoded = base64.b64decode(
                    encoded, validate=True
                ).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError, ValueError):
                # If it looks like Netscape text, treat it as raw instead.
                if "# Netscape HTTP Cookie File" in encoded or (
                    "\t" in encoded and "\n" in encoded
                ):
                    decoded = encoded
                else:
                    raise ValueError(
                        "YOUTUBE_COOKIES_BASE64 is neither valid Base64 nor "
                        "Netscape cookies text. Paste raw cookies into "
                        "YOUTUBE_COOKIES or use a Base64-encoded value."
                    )
            return cls._write_cookie_data(
                decoded, project_root / "runtime_cookies.txt"
            )

        # Local/Docker fallback. Do not commit this file to Git.
        if default_path.is_file() and default_path.stat().st_size > 0:
            cls._validate_cookie_text(default_path.read_text(encoding="utf-8"))
            return {"cookiefile": str(default_path.resolve())}

        return {}

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
            "format": "bestaudio/best/18/best",
            # yt-dlp's JavaScript challenge solver needs both the EJS remote
            # component and an installed JS runtime. Node is installed by the
            # project Dockerfile; detect it rather than assuming it exists.
            "remote_components": {"ejs:github"},
            "extractor_args": {"youtube": {"pot_trace": ["true"]}},
        }
        if shutil.which("node"):
            options["js_runtimes"] = {"node": {}}
        elif shutil.which("deno"):
            options["js_runtimes"] = {"deno": {}}
        elif shutil.which("bun"):
            options["js_runtimes"] = {"bun": {}}

        # Turn on detailed yt-dlp diagnostics only when explicitly requested.
        # This exposes provider/token generation status without noisy logs by default.
        if os.getenv("YOUTUBE_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}:
            options.update({"verbose": True, "quiet": False, "no_warnings": False})

        # Invalid or expired optional cookies must not disable YouTube playback.
        try:
            options.update(cls._cookie_options())
        except (OSError, ValueError, UnicodeError) as exc:
            logging.getLogger(__name__).warning(
                "Ignoring invalid YouTube cookies (%s); trying without cookies.", exc
            )
        options.update(kwargs)
        return options

    @classmethod
    def _retry_profiles(cls, options):
        """Try default, WebPO/mweb with WPC, then token-free Android VR.

        The WPC provider can mint video-bound GVS PO tokens for mweb. The
        Android VR profile is kept as a final fallback and deliberately drops
        account cookies because that client does not support them.
        """
        base = dict(options or {})
        extractor_args = dict(base.get("extractor_args") or {})
        youtube_args = dict(extractor_args.get("youtube") or {})
        youtube_args.pop("player_client", None)
        youtube_args["pot_trace"] = ["true"]
        extractor_args["youtube"] = youtube_args
        base["extractor_args"] = extractor_args

        profiles = [base]
        chromium = (
            os.getenv("CHROME_BIN", "").strip()
            or shutil.which("chromium")
            or shutil.which("chromium-browser")
            or shutil.which("google-chrome")
        )

        # The WPC provider is installed in requirements.txt. Only add this
        # profile when the Docker image has a browser available for token minting.
        if chromium:
            mweb = dict(base)
            mweb_args = dict(mweb.get("extractor_args") or {})
            mweb_youtube = dict(mweb_args.get("youtube") or {})
            mweb_youtube["player_client"] = ["mweb"]
            mweb_youtube["pot_trace"] = ["true"]
            mweb_args["youtube"] = mweb_youtube
            mweb_args["youtubepot-wpc"] = {"browser_path": chromium}
            mweb["extractor_args"] = mweb_args
            profiles.append(mweb)

        android_vr = dict(base)
        android_vr.pop("cookiefile", None)
        android_extractor_args = dict(android_vr.get("extractor_args") or {})
        android_youtube_args = dict(
            android_extractor_args.get("youtube") or {}
        )
        android_youtube_args["player_client"] = ["android_vr"]
        android_youtube_args["pot_trace"] = ["true"]
        android_extractor_args["youtube"] = android_youtube_args
        android_vr["extractor_args"] = android_extractor_args
        profiles.append(android_vr)

        return profiles

    @staticmethod
    def _retryable_error(exc):
        # yt-dlp normally wraps network failures in DownloadError, but some
        # networking backends can surface HTTPError directly. Handle both.
        message = str(exc).lower()
        return any(token in message for token in (
            "403", "forbidden", "requested format is not available",
            "no video formats found", "only images are available",
            "http error 429", "too many requests",
        ))

    @staticmethod
    def _error_label(exc):
        message = str(exc).lower()
        if "403" in message or "forbidden" in message:
            return "HTTP 403 Forbidden"
        if "429" in message or "too many requests" in message:
            return "HTTP 429 Too Many Requests"
        if "format" in message:
            return "format unavailable"
        return type(exc).__name__

    @classmethod
    def _extract(cls, url, download=False, options=None):
        """Extract/download YouTube data with client and PO-token fallbacks."""
        logger = logging.getLogger(__name__)
        profiles = cls._retry_profiles(options)
        last_error = None

        for index, profile in enumerate(profiles, start=1):
            try:
                with yt_dlp.YoutubeDL(profile) as ydl:
                    return ydl.extract_info(url, download=download)
            except Exception as exc:
                last_error = exc
                if not cls._retryable_error(exc) or index == len(profiles):
                    raise
                logger.warning(
                    "YouTube extraction profile %s/%s failed (%s); trying fallback.",
                    index, len(profiles), cls._error_label(exc),
                )

        if last_error:
            raise last_error
        raise RuntimeError("YouTube extraction failed without an error response.")

    async def exists(self, link, videoid=None):
        if not link:
            return False
        if videoid:
            link = self.base + str(link)
        return bool(re.search(self.regex, str(link), re.I))

    async def valid(self, link):
        return await self.exists(link)

    async def url(self, message):
        messages = [message, message.reply_to_message]
        for msg in messages:
            if not msg:
                continue
            text = msg.text or msg.caption or ""
            entities = msg.entities or msg.caption_entities or []
            for entity in entities:
                if entity.type == MessageEntityType.URL:
                    return text[entity.offset:entity.offset + entity.length]
                if entity.type == MessageEntityType.TEXT_LINK:
                    return entity.url
            match = re.search(
                r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/\S+",
                text, re.I,
            )
            if match:
                return match.group(0).rstrip(".,)")
        return None

    async def search(self, query):
        loop = asyncio.get_running_loop()

        def _search():
            info = self._extract(
                f"ytsearch5:{query}",
                options=self._options(extract_flat=True),
            )
            results = []
            for item in info.get("entries") or []:
                if not item:
                    continue
                video_id = item.get("id")
                if not video_id:
                    continue
                duration = self._seconds(item.get("duration"))
                results.append({
                    "title": item.get("title") or "Unknown",
                    "link": self.base + video_id,
                    "duration": self._duration(duration),
                    "duration_sec": duration,
                    "videoid": video_id,
                    "thumbnail": item.get("thumbnail")
                    or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                })
            return results

        return await loop.run_in_executor(None, _search)

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
                options=self._options(format="bestaudio/best", extract_flat=False),
            )
            vidid = info.get("id")
            if not vidid:
                raise ValueError("YouTube video ID not found.")
            duration_sec = self._seconds(info.get("duration"))
            details = {
                "title": info.get("title") or "Unknown",
                "link": info.get("webpage_url") or self.base + vidid,
                "vidid": vidid,
                "videoid": vidid,
                "duration_min": self._duration(duration_sec),
                "duration_sec": duration_sec,
                "thumb": info.get("thumbnail")
                or f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg",
            }
            return details, vidid

        return await loop.run_in_executor(None, _track)

    async def details(self, link, videoid=False):
        details, vidid = await self.track(link, videoid)
        return (
            details["title"], details["duration_min"],
            details["duration_sec"], details["thumb"], vidid,
        )

    async def playlist(self, link, limit=25, user_id=None):
        loop = asyncio.get_running_loop()

        def _playlist():
            info = self._extract(
                link,
                options=self._options(noplaylist=False, extract_flat=True),
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
                raise ValueError("Playlist is empty or unavailable.")
            return results

        return await loop.run_in_executor(None, _playlist)

    async def download(self, link, mystic=None, video=False, videoid=False):
        if videoid:
            link = self.base + str(link)
        loop = asyncio.get_running_loop()

        def _download():
            options = self._options(
                outtmpl=str(self.download_dir / "%(id)s.%(ext)s"),
                noplaylist=True, continuedl=True, nopart=False, overwrites=False,
            )
            if video:
                options["format"] = (
                    "best[height<=720][ext=mp4]/"
                    "best[height<=720]/18/best"
                )
                options["merge_output_format"] = "mp4"
            else:
                options["format"] = "bestaudio/best"
                options["postprocessors"] = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            logger = logging.getLogger(__name__)
            profiles = self._retry_profiles(options)
            last_error = None

            for index, profile in enumerate(profiles, start=1):
                try:
                    with yt_dlp.YoutubeDL(profile) as ydl:
                        info = ydl.extract_info(link, download=True)
                        if not info:
                            raise ValueError("YouTube download returned no data.")

                        video_id = info.get("id")
                        if not video_id:
                            raise ValueError("YouTube video ID missing.")

                        if video:
                            path = Path(ydl.prepare_filename(info))
                            if not path.exists():
                                candidates = [
                                    p for p in self.download_dir.glob(f"{video_id}.*")
                                    if p.suffix.lower() not in (".part", ".ytdl")
                                ]
                                if not candidates:
                                    raise FileNotFoundError(
                                        "Downloaded video file not found."
                                    )
                                # Prefer the merged MP4 when yt-dlp created one.
                                mp4_files = [
                                    p for p in candidates if p.suffix.lower() == ".mp4"
                                ]
                                path = mp4_files[0] if mp4_files else candidates[0]
                        else:
                            path = self.download_dir / f"{video_id}.mp3"

                        if not path.is_file():
                            raise FileNotFoundError(
                                f"Downloaded file missing: {path}"
                            )
                        return str(path.resolve())

                except Exception as exc:
                    last_error = exc
                    if not self._retryable_error(exc) or index == len(profiles):
                        raise
                    logger.warning(
                        "YouTube media download profile %s/%s failed (%s); "
                        "trying fallback.",
                        index, len(profiles), self._error_label(exc),
                    )

            if last_error:
                raise last_error
            raise RuntimeError("YouTube download failed without an error response.")

        file_path = await loop.run_in_executor(None, _download)
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
                        format="best[height<=720][vcodec!=none]/best[height<=720]/best",
                        extract_flat=False,
                    ),
                )
                return info.get("url")

            stream_url = await loop.run_in_executor(None, _get_url)
            if stream_url:
                return 1, stream_url
            return 0, "Unable to fetch YouTube stream URL."
        except Exception as exc:
            return 0, f"Unable to fetch YouTube stream URL: {exc}"
