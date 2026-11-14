import re
from os import getenv

from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()


def _env_int(name, default=None, *, required=False):
    value = getenv(name)
    if value is None or not value.strip():
        if required:
            raise RuntimeError(
                f"Missing required environment variable: {name}. "
                "Set it in your hosting provider's environment settings."
            )
        return default
    try:
        return int(value.strip())
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid value for {name}: expected an integer."
        ) from exc


def _env_bool(name, default=False):
    value = getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Telegram API credentials: https://my.telegram.org/apps
API_ID = _env_int("API_ID", required=True)
API_HASH = getenv("API_HASH")
BOT_TOKEN = getenv("BOT_TOKEN")

if not API_HASH:
    raise RuntimeError("Missing required environment variable: API_HASH.")
if not BOT_TOKEN:
    raise RuntimeError("Missing required environment variable: BOT_TOKEN.")

# Database
MONGO_DB_URI = getenv("MONGO_DB_URI")

# Playback limits
DURATION_LIMIT_MIN = _env_int("DURATION_LIMIT", 300)

# Optional activity log chat. The bot works without a logger group.
LOGGER_ID = _env_int("LOGGER_ID", 0)

# Keep the configured owner ID and all assistant accounts supported.
OWNER_ID = _env_int("OWNER_ID", 8250224070)

# Optional Heroku integration
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "https://github.com/GOVIND-BOTS/AppleMusic",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN")

SUPPORT_CHANNEL = getenv(
    "SUPPORT_CHANNEL", "https://t.me/GOVIND_USERBOT_SUPPORT"
)
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/GOVIND_BOTS")

AUTO_LEAVING_ASSISTANT = _env_bool("AUTO_LEAVING_ASSISTANT", True)

# Spotify credentials are optional; Spotify links can be disabled without them.
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")

PLAYLIST_FETCH_LIMIT = _env_int("PLAYLIST_FETCH_LIMIT", 25)
TG_AUDIO_FILESIZE_LIMIT = _env_int("TG_AUDIO_FILESIZE_LIMIT", 204857600)
TG_VIDEO_FILESIZE_LIMIT = _env_int("TG_VIDEO_FILESIZE_LIMIT", 2073741824)

# Up to five Pyrogram assistant sessions.
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


DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:360"))

for setting_name, setting_value in (
    ("SUPPORT_CHANNEL", SUPPORT_CHANNEL),
    ("SUPPORT_CHAT", SUPPORT_CHAT),
):
    if setting_value and not re.match(r"^https?://", setting_value):
        raise SystemExit(
            f"[ERROR] - Your {setting_name} URL is invalid. "
            "It must start with http:// or https://."
        )
