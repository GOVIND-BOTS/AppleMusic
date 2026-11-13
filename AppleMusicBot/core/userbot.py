
from pyrogram import Client

import config

from ..logging import LOGGER

assistants = []
assistantids = []


class Userbot(Client):
    def __init__(self):
        self.one = Client(
            name="AnonXAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=True,
        )

        self.two = Client(
            name="AnonXAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
            no_updates=True,
        )

        self.three = Client(
            name="AnonXAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
            no_updates=True,
        )

        self.four = Client(
            name="AnonXAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
            no_updates=True,
        )

        self.five = Client(
            name="AnonXAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
            no_updates=True,
        )

        self._clients = [
            (1, self.one, config.STRING1),
            (2, self.two, config.STRING2),
            (3, self.three, config.STRING3),
            (4, self.four, config.STRING4),
            (5, self.five, config.STRING5),
        ]

        self._started_clients = []

    async def start(self):
        LOGGER(__name__).info("Starting Assistants...")

        assistants.clear()
        assistantids.clear()

        for number, client, session in self._clients:
            if not session:
                continue

            try:
                await client.start()
                self._started_clients.append(client)

                me = client.me

                client.id = me.id
                client.name = me.mention
                client.username = me.username

                assistants.append(number)
                assistantids.append(me.id)

                LOGGER(__name__).info(
                    f"Assistant {number} Started as {me.mention}"
                )

                # Join configured groups using the correct assistant.
                for chat in ("GOVIND_BOTS", "GOVIND_USERBOT_UPDATE"):
                    try:
                        await client.join_chat(chat)
                    except Exception as ex:
                        LOGGER(__name__).warning(
                            f"Assistant {number} could not join {chat}: {ex}"
                        )

                # Logger message is optional.
                logger_id = getattr(config, "LOGGER_ID", None)

                if logger_id:
                    try:
                        await client.send_message(
                            logger_id,
                            f"Assistant {number} Started"
                        )
                    except Exception as ex:
                        LOGGER(__name__).warning(
                            f"Assistant {number} could not send "
                            f"startup message to LOGGER_ID: {ex}"
                        )

            except Exception as ex:
                LOGGER(__name__).error(
                    f"Assistant {number} failed to start: {ex}"
                )
                raise

        LOGGER(__name__).info(
            f"Assistants Started: {len(self._started_clients)}"
        )

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")

        for client in reversed(self._started_clients):
            try:
                await client.stop()
                LOGGER(__name__).info(
                    f"Assistant {client.me.id} stopped successfully."
                )
            except Exception as ex:
                LOGGER(__name__).warning(
                    f"Error stopping assistant: {ex}"
                )

        self._started_clients.clear()
        assistants.clear()
        assistantids.clear()

        LOGGER(__name__).info("All Assistants Stopped.")
