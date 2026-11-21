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


def _animated_frame(cover, avatar, title, bot_name, palette, frame_no, template=None):
    if template is not None:
        canvas = template.copy().convert("RGBA")
    else:
        base = ImageOps.fit(cover, (1280, 720)).convert("RGB")
        base = ImageEnhance.Brightness(base.filter(ImageFilter.GaussianBlur(34))).enhance(0.28)
        canvas = base.convert("RGBA")
        canvas.alpha_composite(Image.new("RGBA", canvas.size, (*palette[0], 105)))
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Animated neon glow around the template's large video circle.
    cx, cy, radius = 646, 320, 197
    for width in (18, 11, 5):
        color = palette[(frame_no + width // 5) % len(palette)]
        draw.ellipse((cx-radius-width, cy-radius-width, cx+radius+width, cy+radius+width),
                     outline=(*color, 100 + (frame_no % 3) * 45), width=width)

    # Animated equalizer accents along the lower edge.
    for x in range(22, 1258, 25):
        height = 10 + int((0.5 + 0.5 * math.sin(x / 43 + frame_no * 0.72)) * 32)
        color = palette[(x // 25 + frame_no) % len(palette)]
        draw.rounded_rectangle((x, 713-height, x+7, 713), radius=3, fill=(*color, 190))

    # The large hole in the supplied anime frame is the video/song cover.
    _circle(canvas, cover, 462, 136, 368, ring=(255, 255, 255, 245), border=3)
    # The small overlapping hole is the requesting user's Telegram profile photo.
    _circle(canvas, avatar or cover, 712, 427, 104,
            ring=(*palette[(frame_no + 2) % len(palette)], 255), border=6)

    draw = ImageDraw.Draw(canvas, "RGBA")
    _rainbow_text(draw, bot_name, 58, _font(43, True))
    draw.text((640, 606), "NOW PLAYING", font=_font(23, True), anchor="mm",
              fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 230))
    short_title = title if len(title) <= 44 else title[:41].rstrip() + "..."
    draw.text((640, 641), short_title, font=_font(22, True), anchor="mm",
              fill=(255, 255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 230))
    draw.text((640, 686), "POWERED BY GOVIND-BOTS", font=_font(19, True),
              anchor="mm", fill=(*palette[(frame_no + 1) % len(palette)], 255),
              stroke_width=2, stroke_fill=(0, 0, 0, 230))
    return canvas.convert("RGB")

async def get_thumb(videoid, user_id, thumbnail_url=None, track_title=None):
    """Create a randomly themed animated Now Playing GIF."""
    output = CACHE / f"{videoid}_{user_id}_v5_{random.randrange(1, 1_000_000_000)}.gif"
    if output.is_file():
        return str(output)

    try:
        item = {}
        if not thumbnail_url or not track_title:
            search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
            items = (await search.next()).get("result", [])
            item = items[0] if items else {}
        title = re.sub(r"\s+", " ", track_title or item.get("title", "Unknown Track")).strip()
        thumb_url = thumbnail_url or item.get("thumbnails", [{}])[0].get("url", "")
        if not thumb_url:
            return YOUTUBE_IMG_URL

        cover_path = CACHE / f"cover_{videoid}.jpg"
        await _download(thumb_url.split("?")[0], cover_path)
        with Image.open(cover_path) as source:
            cover = source.convert("RGB")

        avatar = await _avatar(user_id)
        template = None
        if TEMPLATE.is_file():
            try:
                with Image.open(TEMPLATE) as source:
                    source.load()
                    template = ImageOps.fit(
                        source.convert("RGBA"), (1280, 720),
                        method=Image.Resampling.LANCZOS
                    )
            except (OSError, ValueError) as template_error:
                LOGGER(__name__).warning(
                    "Invalid anime thumbnail template %s; using fallback art: %s",
                    TEMPLATE, template_error
                )
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
            _animated_frame(cover, avatar, title, bot_name, palette, index, template)
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
