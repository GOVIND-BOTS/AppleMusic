import os
import re
import math
import random
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
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


def _rainbow_text(draw, text, y, font):
    palette = [
        (255, 70, 115, 255),
        (255, 170, 55, 255),
        (255, 245, 105, 255),
        (80, 235, 160, 255),
        (80, 175, 255, 255),
        (205, 115, 255, 255),
    ]
    widths = [draw.textlength(char, font=font) for char in text]
    x = (1280 - sum(widths)) / 2
    for index, (char, width) in enumerate(zip(text, widths)):
        draw.text(
            (x, y), char, font=font, anchor="lm",
            fill=palette[index % len(palette)],
            stroke_width=3, stroke_fill=(10, 10, 18, 255),
        )
        x += width


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


def _animated_frame(cover, avatar, title, bot_name, palette, frame_no):
    base = ImageOps.fit(cover, (1280, 720)).convert("RGB")
    base = base.filter(ImageFilter.GaussianBlur(34))
    base = ImageEnhance.Brightness(base).enhance(0.28)
    canvas = base.convert("RGBA")
    tint = Image.new("RGBA", canvas.size, (*palette[0], 105))
    canvas.alpha_composite(tint)
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Neon equalizer columns and floating particles.
    for x in range(28, 1255, 28):
        height = 18 + int((0.5 + 0.5 * math.sin((x / 47) + frame_no * 0.7)) * 62)
        draw.rounded_rectangle((x, 690-height, x+8, 690), radius=4,
                               fill=(*palette[(x // 28) % len(palette)], 175))
    for i in range(34):
        x = (i * 137 + frame_no * (7 + i % 5)) % 1280
        y = (i * 83 + frame_no * 11) % 720
        draw.ellipse((x, y, x+3, y+3), fill=(*palette[i % len(palette)], 190))

    # Central video cover and animated rainbow/neon ring.
    cx, cy, radius = 640, 342, 218
    for width in (20, 12, 5):
        bbox = (cx-radius-width, cy-radius-width, cx+radius+width, cy+radius+width)
        draw.ellipse(bbox, outline=(*palette[(frame_no + width//5) % len(palette)], 170), width=width)
    _circle(canvas, cover, cx-radius+8, cy-radius+8, (radius-8)*2,
            ring=(255, 255, 255, 245), border=5)

    # Requester's DP overlaps the lower-right edge of the large circle.
    _circle(canvas, avatar or cover, 790, 458, 112,
            ring=(*palette[(frame_no + 2) % len(palette)], 255), border=7)

    draw = ImageDraw.Draw(canvas, "RGBA")
    _rainbow_text(draw, bot_name, 58, _font(48, True))
    draw.text((640, 612), "NOW PLAYING", font=_font(25, True), anchor="mm",
              fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 230))
    short_title = title if len(title) <= 46 else title[:43].rstrip() + "..."
    draw.text((640, 650), short_title, font=_font(24, True), anchor="mm",
              fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 230))
    draw.text((640, 696), "POWERED BY GOVIND-BOTS", font=_font(19, True),
              anchor="ms", fill=(*palette[(frame_no + 1) % len(palette)], 255),
              stroke_width=2, stroke_fill=(0, 0, 0, 230))
    return canvas.convert("RGB")


async def get_thumb(videoid, user_id, thumbnail_url=None, track_title=None):
    """Create a randomly themed animated Now Playing GIF."""
    output = CACHE / f"{videoid}_{user_id}_v5.gif"
    if output.is_file():
        return str(output)

    try:
        item = {}
        if not thumbnail_url or not track_title:
            search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
            items = (await search.next()).get("result", [])
            item = items[0] if items else {}
        title = re.sub(r"\\s+", " ", track_title or item.get("title", "Unknown Track")).strip()
        thumb_url = thumbnail_url or item.get("thumbnails", [{}])[0].get("url", "")
        if not thumb_url:
            return YOUTUBE_IMG_URL

        cover_path = CACHE / f"cover_{videoid}.jpg"
        await _download(thumb_url.split("?")[0], cover_path)
        with Image.open(cover_path) as source:
            cover = source.convert("RGB")

        avatar = await _avatar(user_id)
        bot = getattr(app, "me", None)
        bot_name = (getattr(bot, "first_name", None) or getattr(app, "name", None)
                    or "ADISHA MUSIC").upper()[:26]
        themes = [
            [(255, 35, 75), (255, 125, 25), (255, 220, 65), (255, 70, 150)],
            [(170, 55, 255), (255, 45, 210), (75, 115, 255), (40, 225, 255)],
            [(0, 190, 255), (40, 255, 210), (90, 130, 255), (210, 80, 255)],
            [(255, 50, 170), (255, 130, 45), (110, 255, 90), (60, 190, 255)],
            [(255, 70, 70), (255, 210, 45), (70, 255, 150), (70, 150, 255)],
        ]
        palette = random.choice(themes)
        frames = [
            _animated_frame(cover, avatar, title, bot_name, palette, index)
            for index in range(8)
        ]
        frames[0].save(
            output, save_all=True, append_images=frames[1:],
            duration=110, loop=0, optimize=True, disposal=2
        )
        return str(output)
    except Exception as exc:
        LOGGER(__name__).exception("Now Playing thumbnail generation failed for %s: %s", videoid, exc)
        return YOUTUBE_IMG_URL
