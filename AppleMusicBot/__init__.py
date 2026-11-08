from AppleMusicBot.core.bot import AppleBot
from AppleMusicBot.core.dir import dirr
from AppleMusicBot.core.userbot import Userbot
from AppleMusicBot.misc import db, sudo

from .logging import LOGGER

dirr()

app = AppleBot()
userbot = Userbot()

from AppleMusicBot.platforms import (
    AppleAPI,
    RessoAPI,
    SoundAPI,
    SpotifyAPI,
    TelegramAPI,
    YouTubeAPI,
)

YouTube = YouTubeAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Apple = AppleAPI()
Resso = RessoAPI()
Telegram = TelegramAPI()

LOGGER(__name__).info("AppleMusic platforms loaded.")
