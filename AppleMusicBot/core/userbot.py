from pyrogram import Client

import config

from ..logging import LOGGER

assistants = []
assistantids = []


class Userbot:
    def __init__(self):
        # Keep stable attributes because the database helper maps assistant
        # numbers to these names. Unconfigured sessions remain None.
        self.one = self._make_client("AnonXAss1", config.STRING1)
        self.two = self._make_client("AnonXAss2", config.STRING2)
        self.three = self._make_client("AnonXAss3", config.STRING3)
        self.four = self._make_client("AnonXAss4", config.STRING4)
        self.five = self._make_client("AnonXAss5", config.STRING5)

        self._clients = [
            (1, self.one),
            (2, self.two),
            (3, self.three),
            (4, self.four),
            (5, self.five),
        ]
        self._started_clients = []

    @staticmethod
    def _make_client(name, session):
        if not session or not str(session).strip():
            return None
        return Client(
            name=name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(session).strip(),
            no_updates=True,
        )

    async def start(self):
        LOGGER(__name__).info("Starting Assistants...")
        assistants.clear()
        assistantids.clear()
        self._started_clients.clear()

        configured = [(number, client) for number, client in self._clients if client]
        if not configured:
            LOGGER(__name__).warning(
                "No assistant session strings configured; music voice-chat "
                "features requiring an assistant will be unavailable."
            )
            return

        for number, client in configured:
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
                    f"Assistant {number} started as {me.mention}"
                )

                for chat in ("GOVIND_BOTS", "GOVIND_USERBOT_UPDATE"):
                    try:
                        await client.join_chat(chat)
                    except Exception as exc:
                        LOGGER(__name__).warning(
                            f"Assistant {number} could not join {chat}: "
                            f"{type(exc).__name__}: {exc}"
                        )

                logger_id = getattr(config, "LOGGER_ID", 0)
                if logger_id:
                    try:
                        await client.send_message(
                            logger_id, f"Assistant {number} Started"
                        )
                    except Exception as exc:
                        LOGGER(__name__).warning(
                            f"Assistant {number} could not send optional "
                            f"startup log: {type(exc).__name__}: {exc}"
                        )

            except Exception as exc:
                LOGGER(__name__).exception(
                    f"Assistant {number} failed to start: "
                    f"{type(exc).__name__}: {exc}"
                )
                # One bad session should not prevent other configured
                # assistants from starting.
                continue

        LOGGER(__name__).info(
            f"Assistants started successfully: {len(self._started_clients)}"
        )

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")
        for client in reversed(self._started_clients):
            try:
                await client.stop()
                LOGGER(__name__).info(
                    f"Assistant {client.me.id} stopped successfully."
                )
            except Exception as exc:
                LOGGER(__name__).warning(
                    f"Error stopping assistant: {type(exc).__name__}: {exc}"
                )

        self._started_clients.clear()
        assistants.clear()
        assistantids.clear()
        LOGGER(__name__).info("All Assistants Stopped.")
