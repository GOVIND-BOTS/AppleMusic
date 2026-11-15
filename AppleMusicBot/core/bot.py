from pathlib import Path
import asyncio

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait

import config

from ..logging import LOGGER


# Keep the bot's authorized MTProto session across restarts when the host has
# persistent storage. This avoids repeatedly importing bot authorization.
_BOT_SESSION_FILE = Path("cache/bot_session.str")


class AppleBot(Client):
    def __init__(self):
        LOGGER(__name__).info("Starting Bot...")

        session_string = None
        try:
            if _BOT_SESSION_FILE.is_file():
                session_string = _BOT_SESSION_FILE.read_text(encoding="utf-8").strip() or None
        except Exception as exc:
            LOGGER(__name__).warning(
                "Could not read cached bot session: %s: %s",
                type(exc).__name__,
                exc,
            )

        super().__init__(
            name="AppleMusicBot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            session_string=session_string,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=7,
        )

    async def start(self):
        # Telegram may temporarily rate-limit bot authorization. Retry only
        # FloodWait; do not hide network/authentication errors.
        for attempt in range(12):
            try:
                await super().start()
                break
            except FloodWait as exc:
                wait_seconds = int(exc.value) + 5
                LOGGER(__name__).warning(
                    "Bot authorization FloodWait (%s/12); retrying in %s seconds.",
                    attempt + 1,
                    wait_seconds,
                )
                await asyncio.sleep(wait_seconds)
        else:
            raise RuntimeError(
                "Bot authorization kept returning FloodWait; startup aborted."
            )

        # Save only after Telegram has successfully authorized this client.
        try:
            if not _BOT_SESSION_FILE.is_file():
                _BOT_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
                _BOT_SESSION_FILE.write_text(
                    await self.export_session_string(),
                    encoding="utf-8",
                )
                LOGGER(__name__).info("Bot session cache created.")
        except Exception as exc:
            LOGGER(__name__).warning(
                "Could not persist bot session cache: %s: %s",
                type(exc).__name__,
                exc,
            )

        self.id = self.me.id
        self.name = (
            self.me.first_name + " " + (self.me.last_name or "")
        ).strip()
        self.username = self.me.username
        self.mention = self.me.mention

        LOGGER(__name__).info(
            "Bot started successfully: %s (@%s)",
            self.name,
            self.username,
        )

        # Logger group is optional; it must never prevent the bot from serving
        # commands when LOGGER_ID is unset or inaccessible.
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
        except Exception as exc:
            LOGGER(__name__).warning(
                "Could not send startup message to LOGGER_ID. "
                "Bot will continue running. Reason: %s - %s",
                type(exc).__name__,
                exc,
            )

    async def stop(self):
        LOGGER(__name__).info("Stopping AppleMusicBot...")
        await super().stop()
