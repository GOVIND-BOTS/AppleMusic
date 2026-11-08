from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus

import config
from AppleMusic.logging import LOGGER


class AppleBot(Client):
    def __init__(self):
        super().__init__(
            name="AppleMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention
        try:
            await self.send_message(
                config.LOGGER_ID,
                f"**{config.BOT_NAME} bot started.**\nID: `{self.id}`",
            )
        except Exception:
            LOGGER(__name__).warning("Logger chat not reachable. Check LOGGER_ID.")
        if config.LOGGER_ID:
            try:
                chat = await self.get_chat(config.LOGGER_ID)
                LOGGER(__name__).info(f"Logger chat: {chat.title or chat.id}")
            except Exception:
                pass
        LOGGER(__name__).info(f"Bot started as {self.name} (@{self.username})")

    async def stop(self):
        await super().stop()
