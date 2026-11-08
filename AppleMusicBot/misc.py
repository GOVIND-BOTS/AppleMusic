import time
from pyrogram import filters

from config import OWNER_ID

SUDOERS = filters.user()
SUDOERS.add(OWNER_ID)

db = {}
sudo = {"owners": [OWNER_ID]}
START_TIME = time.time()
