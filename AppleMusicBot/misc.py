import socket
import time

import heroku3
from pyrogram import filters

import config
from AppleMusicBot.core.mongo import mongodb

from .logging import LOGGER

SUDOERS = filters.user()
HAPP = None
_boot_ = time.time()


def is_heroku():
    """Return True only when this process is running on Heroku."""
    return "heroku" in socket.getfqdn().lower()


def dbb():
    global db
    db = {}
    LOGGER(__name__).info("Local Database Initialized.")


async def sudo():
    SUDOERS.add(config.OWNER_ID)

    sudoersdb = mongodb.sudoers
    document = await sudoersdb.find_one({"sudo": "sudo"})
    sudoers = [] if not document else document.get("sudoers", [])

    if config.OWNER_ID not in sudoers:
        sudoers.append(config.OWNER_ID)
        await sudoersdb.update_one(
            {"sudo": "sudo"},
            {"$set": {"sudoers": sudoers}},
            upsert=True,
        )

    for user_id in sudoers:
        try:
            SUDOERS.add(int(user_id))
        except (TypeError, ValueError):
            LOGGER(__name__).warning(
                f"Ignoring invalid sudo user ID in database: {user_id!r}"
            )

    LOGGER(__name__).info("Sudoers Loaded.")


def heroku():
    """Initialize the optional Heroku API client once at startup."""
    global HAPP
    if not is_heroku():
        return

    if not config.HEROKU_API_KEY or not config.HEROKU_APP_NAME:
        LOGGER(__name__).warning(
            "Heroku API credentials are not configured; Heroku controls disabled."
        )
        return

    try:
        heroku_client = heroku3.from_key(config.HEROKU_API_KEY)
        HAPP = heroku_client.app(config.HEROKU_APP_NAME)
        LOGGER(__name__).info("Heroku App Configured.")
    except Exception as exc:
        HAPP = None
        LOGGER(__name__).warning(
            "Could not configure Heroku integration: "
            f"{type(exc).__name__}: {exc}"
        )
