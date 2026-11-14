import socket
import time

import heroku3
from pyrogram import filters

import config
from AppleMusicBot.core.mongo import mongodb, ping_mongo

from .logging import LOGGER

SUDOERS = filters.user()

HAPP = None
_boot_ = time.time()


def is_heroku():
    return "heroku" in socket.getfqdn().lower()


XCB = [
    "/",
    "@",
    ".",
    "com",
    ":",
    "git",
    "heroku",
    "push",
    "https",
    "HEAD",
    "master",
]


def dbb():
    global db
    db = {}
    LOGGER(__name__).info("Local Database Initialized.")


async def sudo():
    global SUDOERS

    # Check the database before reading or writing sudoers.
    await ping_mongo()

    SUDOERS.add(config.OWNER_ID)
    sudoersdb = mongodb.sudoers
    sudoers = await sudoersdb.find_one({"sudo": "sudo"})
    sudoers = [] if not sudoers else sudoers.get("sudoers", [])

    if config.OWNER_ID not in sudoers:
        sudoers.append(config.OWNER_ID)
        await sudoersdb.update_one(
            {"sudo": "sudo"},
            {"$set": {"sudoers": sudoers}},
            upsert=True,
        )

    for user_id in sudoers:
        SUDOERS.add(user_id)

    LOGGER(__name__).info("Sudoers Loaded.")


def heroku():
    global HAPP

    if not is_heroku():
        return

    if not config.HEROKU_API_KEY or not config.HEROKU_APP_NAME:
        LOGGER(__name__).warning(
            "Heroku integration is disabled: HEROKU_API_KEY or "
            "HEROKU_APP_NAME is missing."
        )
        return

    try:
        heroku_client = heroku3.from_key(config.HEROKU_API_KEY)
        HAPP = heroku_client.app(config.HEROKU_APP_NAME)
        LOGGER(__name__).info("Heroku App Configured.")
    except Exception as exc:
        LOGGER(__name__).warning(
            "Could not configure Heroku integration: "
            f"{type(exc).__name__}: {exc}"
        )
