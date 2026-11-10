from AppleMusicBot.core.bot import AppleBot
from AppleMusicBot.core.dir import dirr
from AppleMusicBot.core.userbot import Userbot
from AppleMusicBot.misc import dbb, sudo

from .logging import LOGGER

dirr()
dbb()

app = AppleBot()
userbot = Userbot()

from AppleMusicBot.platforms import (
    AppleAPI,
    CarbonAPI,
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
Carbon = CarbonAPI()

LOGGER(__name__).info("AppleMusic platforms loaded.")
