import os

from AppleMusicBot.logging import LOGGER


def dirr():
    for folder in ("downloads", "cache"):
        os.makedirs(folder, exist_ok=True)
    LOGGER(__name__).info("Directories checked.")
