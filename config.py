import re
from os import getenv

from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()


def _int_env(name, default):
    value = getenv(name)
    if value in (None, ""):
        return int(default)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"[CONFIG ERROR] {name} must be an integer.") from exc


def _bool_env(name, default=False):
    value = getenv(name)
    if value is None:
        return bool(default)
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Telegram API credentials: https://my.telegram.org/apps
API_ID = _int_env("API_ID", 0)
API_HASH = getenv("API_HASH", "").strip()
BOT_TOKEN = getenv("BOT_TOKEN", "").strip()

# MongoDB connection string
MONGO_DB_URI = getenv("MONGO_DB_URI", "").strip()

DURATION_LIMIT_MIN = _int_env("DURATION_LIMIT", 300)
DURATION_LIMIT = DURATION_LIMIT_MIN * 60

LOGGER_ID = _int_env("LOGGER_ID", 0)
OWNER_ID = _int_env("OWNER_ID", 8250224070)

# Heroku deployment credentials (optional)
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/GOVIND-BOTS/AppleMusic",
).strip()
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main").strip() or "main"
GIT_TOKEN = getenv("GIT_TOKEN")

SUPPORT_CHANNEL = getenv(
    "SUPPORT_CHANNEL", "https://t.me/GOVIND_USERBOT_SUPPORT"
).strip()
SUPPORT_CHAT = getenv(
    "SUPPORT_CHAT", "https://t.me/GOVIND_BOTS"
).strip()

AUTO_LEAVING_ASSISTANT = _bool_env("AUTO_LEAVING_ASSISTANT", True)

# Spotify API credentials (optional)
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")

PLAYLIST_FETCH_LIMIT = _int_env("PLAYLIST_FETCH_LIMIT", 25)
TG_AUDIO_FILESIZE_LIMIT = _int_env("TG_AUDIO_FILESIZE_LIMIT", 204857600)
TG_VIDEO_FILESIZE_LIMIT = _int_env("TG_VIDEO_FILESIZE_LIMIT", 2073741824)

# Up to five optional Pyrogram user sessions
STRING1 = getenv("STRING_SESSION")
STRING2 = getenv("STRING_SESSION2")
STRING3 = getenv("STRING_SESSION3")
STRING4 = getenv("STRING_SESSION4")
STRING5 = getenv("STRING_SESSION5")

BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

START_IMG_URL = [
    "https://graph.org/file/6537f82eaef8f90faa91f-fdb34f99a0385ad4b2.jpg"
]
PING_IMG_URL = getenv(
    "PING_IMG_URL", "https://mallucampaign.in/images/img_1692101295.jpg"
)
PLAYLIST_IMG_URL = "https://graph.org/file/c95a687e777b55be1c792.jpg"
STATS_IMG_URL = "https://mallucampaign.in/images/img_1694847936.jpg"
TELEGRAM_AUDIO_URL = "https://graph.org/file/ff2af8d4d10afa1baf49e.jpg"
TELEGRAM_VIDEO_URL = "https://graph.org/file/ff2af8d4d10afa1baf49e.jpg"
STREAM_IMG_URL = "https://graph.org/file/ff2af8d4d10afa1baf49e.jpg"
SOUNCLOUD_IMG_URL = "https://graph.org/file/c95a687e777b55be1c792.jpg"
YOUTUBE_IMG_URL = "https://graph.org/file/e8730fdece86a1166f608.jpg"
SPOTIFY_ARTIST_IMG_URL = "https://graph.org/file/0bb6f36796d496b4254ff.jpg"
SPOTIFY_ALBUM_IMG_URL = "https://graph.org/file/0bb6f36796d496b4254ff.jpg"
SPOTIFY_PLAYLIST_IMG_URL = "https://graph.org/file/0bb6f36796d496b4254ff.jpg"


def time_to_seconds(time):
    stringt = str(time)
    return sum(
        int(part) * 60**index
        for index, part in enumerate(reversed(stringt.split(":")))
    )


if API_ID <= 0:
    raise SystemExit("[CONFIG ERROR] Set a valid numeric API_ID in Railway Variables.")
if not API_HASH:
    raise SystemExit("[CONFIG ERROR] Set API_HASH in Railway Variables.")
if not BOT_TOKEN:
    raise SystemExit("[CONFIG ERROR] Set BOT_TOKEN in Railway Variables.")
if not MONGO_DB_URI:
    raise SystemExit("[CONFIG ERROR] Set MONGO_DB_URI in Railway Variables.")

for name, value in (("SUPPORT_CHANNEL", SUPPORT_CHANNEL), ("SUPPORT_CHAT", SUPPORT_CHAT)):
    if value and not re.fullmatch(r"https?://\\S+", value):
        raise SystemExit(
            f"[CONFIG ERROR] {name} must be a valid URL starting with https://"
        )
