import os
import re
import math
import random
from pathlib import Path

import aiohttp
from PIL import (
    Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont,
    ImageOps
)
from youtubesearchpython.__future__ import VideosSearch

from AppleMusicBot import app
from AppleMusicBot.logging import LOGGER
from config import YOUTUBE_IMG_URL

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
CACHE = Path("cache")
CACHE.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1280, 720
GITHUB_NAME = "GOVIND-BOTS"
GITHUB_URL = "github.com/GOVIND-BOTS/AppleMusic"

THEMES = [
    [(255, 55, 115), (255, 145, 45), (255, 220, 85), (255, 70, 190)],
    [(180, 75, 255), (255, 65, 215), (75, 145, 255), (40, 230, 235)],
    [(0, 195, 255), (45, 255, 205), (100, 125, 255), (225, 80, 255)],
    [(255, 65, 85), (255, 175, 45), (95, 255, 145), (65, 155, 255)],
    [(255, 70, 180), (140, 90, 255), (50, 220, 255), (255, 205, 70)],
    [(255, 100, 40), (255, 45, 130), (170, 70, 255), (55, 220, 220)],
    [(80, 220, 255), (115, 100, 255), (255, 80, 190), (255, 190, 65)],
    [(255, 40, 75), (255, 115, 35), (255, 225, 65), (80, 235, 190)],
]


def _font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        str(ASSETS / ("font2.ttf" if bold else "font.ttf")),
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _fit_text(draw, text, max_width, start_size, bold=True, min_size=18):
    size = start_size
    while size > min_size:
        font = _font(size, bold)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
        size -= 1
    return _font(min_size, bold)


def _download_sync_path(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)


async def _download(url, path):
    timeout = aiohttp.ClientTimeout(total=25)
    headers = {"User-Agent": "Mozilla/5.0 AppleMusicBot/1.0"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.read()
    path.write_bytes(data)


async def _avatar(user_id):
    path = CACHE / f"avatar_{user_id}.jpg"
    for chat_id in (user_id, getattr(app, "id", None)):
        if not chat_id:
            continue
        try:
            async for photo in app.get_chat_photos(chat_id, limit=1):
                saved = await app.download_media(photo.file_id, file_name=str(path))
                if saved and os.path.isfile(saved):
                    with Image.open(saved) as image:
                        image.load()
                        return image.convert("RGB")
        except Exception:
            continue
    return None


def _make_anime_girl(size=440, accent=(255, 80, 190), frame_no=0):
    """Draw an original anime-inspired mascot in memory; no image asset required."""
    art = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(art, "RGBA")
    cx = size // 2
    bob = int(math.sin(frame_no * 0.65) * 4)

    # Back hair and long side locks
    d.ellipse((85, 34 + bob, 355, 340 + bob), fill=(30, 20, 58, 255))
    d.polygon([(115, 130+bob), (75, 335+bob), (120, 395+bob),
               (165, 235+bob)], fill=(35, 24, 72, 255))
    d.polygon([(315, 120+bob), (375, 330+bob), (330, 400+bob),
               (285, 235+bob)], fill=(35, 24, 72, 255))

    # Neck and shoulders
    d.rounded_rectangle((190, 260+bob, 250, 340+bob), radius=20,
                        fill=(255, 205, 190, 255))
    d.ellipse((85, 300+bob, 355, 505+bob), fill=(accent[0], accent[1], accent[2], 245))
    d.polygon([(160, 310+bob), (220, 390+bob), (280, 310+bob),
               (315, 450+bob), (125, 450+bob)], fill=(245, 245, 255, 255))

    # Face
    d.ellipse((125, 75+bob, 315, 315+bob), fill=(255, 220, 205, 255),
              outline=(255, 235, 230, 255), width=5)
    # Fringe
    d.polygon([(118, 185+bob), (105, 90+bob), (155, 48+bob),
               (235, 30+bob), (320, 90+bob), (320, 180+bob),
               (275, 135+bob), (245, 170+bob), (210, 125+bob),
               (175, 175+bob), (145, 140+bob)], fill=(35, 23, 70, 255))
    d.polygon([(130, 112+bob), (165, 55+bob), (210, 42+bob),
               (178, 145+bob)], fill=(95, 65, 150, 255))
    d.polygon([(245, 48+bob), (300, 88+bob), (300, 160+bob),
               (270, 130+bob)], fill=(100, 65, 155, 255))

    # Eyes, shine, blush and smile
    eye_y = 205 + bob
    for ex in (178, 260):
        d.ellipse((ex-19, eye_y-25, ex+19, eye_y+25), fill=(65, 45, 105, 255))
        d.ellipse((ex-9, eye_y-14, ex+8, eye_y+12), fill=(105, 205, 255, 255))
        d.ellipse((ex-5, eye_y-11, ex+2, eye_y-3), fill=(255, 255, 255, 255))
    d.ellipse((140, 240+bob, 177, 254+bob), fill=(255, 125, 145, 95))
    d.ellipse((264, 240+bob, 301, 254+bob), fill=(255, 125, 145, 95))
    d.arc((205, 230+bob, 235, 260+bob), 10, 165, fill=(180, 75, 105, 255), width=4)

    # Headphones and glowing hair accessory
    d.arc((98, 58+bob, 342, 300+bob), 185, 355, fill=(*accent, 255), width=13)
    d.rounded_rectangle((92, 160+bob, 125, 230+bob), radius=12,
                        fill=(*accent, 255), outline=(255, 255, 255, 230), width=3)
    d.rounded_rectangle((315, 160+bob, 348, 230+bob), radius=12,
                        fill=(*accent, 255), outline=(255, 255, 255, 230), width=3)
    d.ellipse((272, 72+bob, 315, 115+bob), fill=(255, 235, 120, 255),
              outline=(255, 255, 255, 255), width=4)
    return art


def _circle(canvas, source, x, y, size, ring, border=6):
    source = ImageOps.fit(source.convert("RGB"), (size, size),
                          method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size-1, size-1), fill=255)
    if border:
        ring_layer = Image.new("RGBA", (size+border*2, size+border*2), (0, 0, 0, 0))
        ImageDraw.Draw(ring_layer).ellipse(
            (0, 0, ring_layer.width-1, ring_layer.height-1), fill=ring
        )
        canvas.alpha_composite(ring_layer, (x-border, y-border))
    canvas.paste(source.convert("RGBA"), (x, y), mask)


def _background(cover, palette, frame_no):
    # The YouTube cover itself becomes a blurred, colourful full-bleed backdrop.
    bg = ImageOps.fit(cover, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(38))
    bg = ImageEnhance.Brightness(bg).enhance(0.32)
    canvas = bg.convert("RGBA")
    tint = Image.new("RGBA", canvas.size, (*palette[frame_no % len(palette)], 85))
    canvas = Image.alpha_composite(canvas, tint)
    shade = Image.new("RGBA", canvas.size, (5, 5, 18, 105))
    return Image.alpha_composite(canvas, shade)


def _animated_frame(cover, avatar, title, bot_name, palette, frame_no):
    canvas = _background(cover, palette, frame_no)
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Premium glass panel
    draw.rounded_rectangle((35, 35, 1245, 685), radius=42,
                           fill=(8, 8, 24, 190),
                           outline=(*palette[frame_no % len(palette)], 220), width=4)

    # Animated neon orbit around the YouTube artwork
    cx, cy, radius = 335, 350, 190
    pulse = int(7 + 7 * math.sin(frame_no * 0.8))
    for j, width in enumerate((16, 9, 4)):
        col = palette[(frame_no + j) % len(palette)]
        draw.ellipse((cx-radius-pulse-j*5, cy-radius-pulse-j*5,
                      cx+radius+pulse+j*5, cy+radius+pulse+j*5),
                     outline=(*col, 125 + j*30), width=width)

    _circle(canvas, cover, 155, 170, 360,
            ring=(*palette[(frame_no+1) % len(palette)], 255), border=8)

    # Anime mascot is generated in memory and gently bobs between GIF frames.
    mascot = _make_anime_girl(440, palette[(frame_no+2) % len(palette)], frame_no)
    canvas.alpha_composite(mascot, (805, 180))

    draw = ImageDraw.Draw(canvas, "RGBA")
    # Header
    draw.rounded_rectangle((585, 65, 1185, 145), radius=24,
                           fill=(4, 5, 18, 225),
                           outline=(*palette[frame_no % len(palette)], 235), width=3)
    brand = bot_name or "ADISHA MUSIC"
    brand_font = _fit_text(draw, brand, 550, 39, True, 24)
    draw.text((885, 105), brand, font=brand_font, anchor="mm",
              fill=(255, 255, 255, 255), stroke_width=2,
              stroke_fill=(0, 0, 0, 255))

    # Clear title area with adaptive font size and two-line wrapping.
    draw.rounded_rectangle((565, 420, 1190, 585), radius=25,
                           fill=(4, 5, 18, 235),
                           outline=(*palette[(frame_no+2) % len(palette)], 230), width=3)
    draw.text((600, 450), "♫  NOW PLAYING", font=_font(23, True),
              fill=(*palette[(frame_no+1) % len(palette)], 255),
              stroke_width=1, stroke_fill=(0, 0, 0, 255))

    clean_title = re.sub(r"\s+", " ", title).strip() or "Unknown Track"
    max_chars = 43
    lines = []
    remaining = clean_title
    while remaining and len(lines) < 2:
        if len(remaining) <= max_chars:
            lines.append(remaining)
            break
        cut = remaining.rfind(" ", 0, max_chars)
        if cut < 12:
            cut = max_chars
        lines.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        lines[-1] = lines[-1].rstrip(" .") + "…"
    if not lines:
        lines = ["Unknown Track"]
    title_font = _fit_text(draw, max(lines, key=len), 555, 31, True, 20)
    if len(lines) == 1:
        draw.text((600, 510), lines[0], font=title_font, fill=(255, 255, 255, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0, 255))
    else:
        draw.text((600, 495), lines[0], font=title_font, fill=(255, 255, 255, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0, 255))
        draw.text((600, 535), lines[1], font=title_font, fill=(255, 255, 255, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0, 255))

    # GitHub identity stays legible and fixed rather than rainbow-per-letter.
    draw.text((600, 605), GITHUB_NAME, font=_font(23, True),
              fill=(255, 255, 255, 255), stroke_width=2,
              stroke_fill=(0, 0, 0, 255))
    draw.text((600, 634), GITHUB_URL, font=_font(16, False),
              fill=(205, 215, 245, 255), stroke_width=1,
              stroke_fill=(0, 0, 0, 255))

    # User profile badge, if Telegram can provide it.
    if avatar is not None:
        _circle(canvas, avatar, 65, 62, 74,
                ring=(*palette[(frame_no+3) % len(palette)], 255), border=4)

    # Safe-width animated equalizer bars (no rounded-rectangle radius overflow).
    draw = ImageDraw.Draw(canvas, "RGBA")
    for x in range(55, 1220, 20):
        height = 4 + int((0.5 + 0.5 * math.sin(x/42 + frame_no*0.75)) * 10)
        color = palette[(x//20 + frame_no) % len(palette)]
        draw.rounded_rectangle((x, 674-height, x+13, 674),
                               radius=3, fill=(*color, 230))

    # Moving sparkles
    for i in range(22):
        px = (i*59 + frame_no*13) % WIDTH
        py = (i*37 + frame_no*9) % HEIGHT
        rr = 2 + (i % 3)
        col = palette[(i+frame_no) % len(palette)]
        draw.ellipse((px-rr, py-rr, px+rr, py+rr), fill=(*col, 170))

    return canvas.convert("RGB")


async def get_thumb(videoid, user_id, thumbnail_url=None, track_title=None):
    """Generate a colourful, randomly themed animated Now Playing GIF."""
    output = CACHE / f"{videoid}_{user_id}_nowplaying_{random.randrange(1, 1_000_000_000)}.gif"

    try:
        item = {}
        if not thumbnail_url or not track_title:
            search = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
            result = await search.next()
            items = result.get("result", []) if isinstance(result, dict) else []
            item = items[0] if items else {}

        title = re.sub(r"\s+", " ", track_title or item.get("title", "Unknown Track")).strip()
        thumb_url = thumbnail_url or (
            (item.get("thumbnails") or [{}])[0].get("url", "")
        )

        cover = None
        if thumb_url:
            try:
                cover_path = CACHE / f"yt_cover_{videoid}.jpg"
                await _download(thumb_url, cover_path)
                with Image.open(cover_path) as source:
                    source.load()
                    cover = source.convert("RGB")
            except Exception as error:
                LOGGER(__name__).warning("YouTube cover download failed for %s: %s", videoid, error)

        if cover is None:
            # Built-in fallback artwork; no template or external image is required.
            cover = Image.new("RGB", (640, 640), (35, 18, 70))
            cd = ImageDraw.Draw(cover)
            for y in range(640):
                t = y / 640
                cd.line((0, y, 640, y),
                        fill=(int(45+90*t), int(20+25*t), int(105+100*(1-t))))
            cd.ellipse((105, 105, 535, 535), outline=(255, 80, 200), width=18)
            cd.text((320, 320), "♪", font=_font(220, True),
                    fill=(255, 255, 255), anchor="mm")

        avatar = await _avatar(user_id)
        me = getattr(app, "me", None)
        bot_name = (
            getattr(me, "first_name", None)
            or getattr(app, "name", None)
            or "ADISHA MUSIC"
        ).upper()[:28]

        palette = random.choice(THEMES)
        frame_count = 12
        frames = [
            _animated_frame(cover, avatar, title, bot_name, palette, index)
            for index in range(frame_count)
        ]

        frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=105,
            loop=0,
            optimize=False,
            disposal=2,
        )
        return str(output)

    except Exception as exc:
        LOGGER(__name__).exception("Now Playing GIF generation failed for %s: %s", videoid, exc)
        return YOUTUBE_IMG_URL
