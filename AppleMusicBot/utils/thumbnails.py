import os
import re
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch

from AppleMusicBot import app
from AppleMusicBot.logging import LOGGER
from config import YOUTUBE_IMG_URL

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TEMPLATE = ASSETS / "nowplaying_template.jpg"
CACHE = Path("cache")
CACHE.mkdir(parents=True, exist_ok=True)


def _font(size, bold=False):
    path = ASSETS / ("font2.ttf" if bold else "font.ttf")
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def _circle(canvas, source, x, y, size, ring=(255, 255, 255, 255), border=5):
    source = ImageOps.fit(source.convert("RGB"), (size, size), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    if border:
        layer = Image.new("RGBA", (size + border * 2, size + border * 2), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse((0, 0, layer.width - 1, layer.height - 1), fill=ring)
        canvas.alpha_composite(layer, (x - border, y - border))
    canvas.paste(source.convert("RGBA"), (x, y), mask)


async def _download(url, path):
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.read()
    path.write_bytes(data)


async def _avatar(user_id):
    path = CACHE / f"avatar_{user_id}.jpg"
    for chat_id in (user_id, app.id):
        try:
            async for photo in app.get_chat_photos(chat_id, limit=1):
                saved = await app.download_media(photo.file_id, file_name=str(path))
                if saved and os.path.isfile(saved):
                    return Image.open(saved).convert("RGB")
        except Exception:
            continue
    return None


async def get_thumb(videoid, user_id, thumbnail_url=None, track_title=None):
    """Build the branded anime-style Now Playing thumbnail."""
    output = CACHE / f"{videoid}_{user_id}_v2.png"
    if output.is_file():
        return str(output)

    try:
        item = {}
        if not thumbnail_url or not track_title:
            search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
            items = (await search.next()).get("result", [])
            item = items[0] if items else {}
        title = re.sub(
            r"\s+",
            " ",
            track_title or item.get("title", "Unknown Track"),
        ).strip()
        thumb_url = thumbnail_url or item.get("thumbnails", [{}])[0].get("url", "")
        if not thumb_url:
            return YOUTUBE_IMG_URL

        cover_path = CACHE / f"cover_{videoid}.jpg"
        await _download(thumb_url.split("?")[0], cover_path)
        cover = Image.open(cover_path).convert("RGB")

        if TEMPLATE.is_file():
            canvas = ImageOps.fit(
                Image.open(TEMPLATE).convert("RGBA"), (1280, 720),
                method=Image.Resampling.LANCZOS
            )
        else:
            # Fallback keeps play working if the optional template image is missing.
            canvas = ImageOps.fit(cover, (1280, 720)).convert("RGBA")
            canvas = canvas.filter(ImageFilter.GaussianBlur(22))

        # Main circle: video/song cover. Small circle: requester Telegram DP.
        _circle(canvas, cover, 470, 145, 352, ring=(255, 255, 255, 255), border=5)
        avatar = await _avatar(user_id)
        _circle(canvas, avatar or cover, 712, 426, 104,
                ring=(70, 245, 155, 255), border=5)

        draw = ImageDraw.Draw(canvas)
        bot_name = (getattr(app, "name", None) or "ADISHA MUSIC").upper()[:26]
        # Multicolour title with a dark outline for readability.
        draw.text((640, 58), bot_name, font=_font(46, True), anchor="mm",
                  fill=(255, 90, 145, 255), stroke_width=3, stroke_fill=(10, 10, 18, 255))
        draw.text((640, 58), bot_name, font=_font(46, True), anchor="mm",
                  fill=(255, 220, 95, 255), stroke_width=1, stroke_fill=(10, 10, 18, 255))
        draw.text((640, 582), "NOW PLAYING", font=_font(22, True), anchor="mm",
                  fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 230))
        short_title = title if len(title) <= 44 else title[:41].rstrip() + "..."
        draw.text((640, 620), short_title, font=_font(24, True), anchor="mm",
                  fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 230))
        draw.text((640, 684), "POWERED BY GOVIND-BOTS", font=_font(19, True),
                  anchor="mm", fill=(255, 205, 225, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0, 230))

        canvas.convert("RGB").save(output, "PNG", optimize=True)
        return str(output)
    except Exception as exc:
        LOGGER(__name__).exception("Now Playing thumbnail generation failed for %s: %s", videoid, exc)
        return YOUTUBE_IMG_URL
