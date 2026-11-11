
from pyrogram import Client
from pyrogram.enums import ParseMode

import config

from ..logging import LOGGER


class AppleBot(Client):
    def __init__(self):
        LOGGER(__name__).info("Starting Bot...")

        super().__init__(
            name="AppleMusicBot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        await super().start()

        self.id = self.me.id
        self.name = (
            self.me.first_name + " " + (self.me.last_name or "")
        ).strip()
        self.username = self.me.username
        self.mention = self.me.mention

        LOGGER(__name__).info(
            f"Bot started successfully: {self.name} (@{self.username})"
        )

        # Logger group is optional.
        logger_id = getattr(config, "LOGGER_ID", None)

        if not logger_id:
            LOGGER(__name__).warning(
                "LOGGER_ID is not configured. Skipping startup log message."
            )
            return

        try:
            await self.send_message(
                chat_id=logger_id,
                text=(
                    f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\n"
                    f"ɪᴅ : <code>{self.id}</code>\n"
                    f"ɴᴀᴍᴇ : {self.name}\n"
                    f"ᴜsᴇʀɴᴀᴍᴇ : @{self.username}"
                ),
            )

            LOGGER(__name__).info("Startup message sent to LOGGER_ID.")

        except Exception as ex:
            LOGGER(__name__).warning(
                "Could not send startup message to LOGGER_ID. "
                f"Bot will continue running. "
                f"Reason: {type(ex).__name__} - {ex}"
            )

    async def stop(self):
        LOGGER(__name__).info("Stopping AppleMusicBot...")
        await super().stop()
