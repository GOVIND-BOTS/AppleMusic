from pyrogram import Client

import config
from AppleMusicBot.logging import LOGGER


class Userbot(Client):
    def __init__(self):
        self.one = Client(
            name="AppleAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=True,
        ) if config.STRING1 else None
        self.two = Client(
            name="AppleAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
            no_updates=True,
        ) if config.STRING2 else None
        self.three = Client(
            name="AppleAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
            no_updates=True,
        ) if config.STRING3 else None
        self.four = Client(
            name="AppleAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
            no_updates=True,
        ) if config.STRING4 else None
        self.five = Client(
            name="AppleAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
            no_updates=True,
        ) if config.STRING5 else None
        self.assistants = []

    async def start(self):
        LOGGER(__name__).info("Starting assistants...")
        for client in (self.one, self.two, self.three, self.four, self.five):
            if not client:
                continue
            try:
                await client.start()
                me = client.me
                self.assistants.append(client)
                LOGGER(__name__).info(f"Assistant started: {me.first_name} ({me.id})")
            except Exception as e:
                LOGGER(__name__).error(f"Assistant failed: {e}")
        if not self.assistants:
            LOGGER(__name__).error("No assistant started. Set STRING_SESSION.")
            raise SystemExit("STRING_SESSION required for voice chat playback.")

    async def stop(self):
        for client in self.assistants:
            try:
                await client.stop()
            except Exception:
                pass
