from AppleMusic.core.bot import AppleBot
from AppleMusic.core.dir import dirr
from AppleMusic.core.userbot import Userbot
from AppleMusic.misc import db, sudo

from .logging import LOGGER

dirr()

app = AppleBot()
userbot = Userbot()

from AppleMusic.platforms import (
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
