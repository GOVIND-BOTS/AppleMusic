
from pyrogram import Client
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import (
    HighQualityAudio,
    MediumQualityVideo,
)

from AppleMusicBot.logging import LOGGER
from AppleMusicBot.utils.stream.queue import (
    clear_queue,
    get_current_track,
    pop_current,
)


class AppleCall:
    def __init__(self):
        self.calls = {}
        self.registered = set()

    def get_call(self, client: Client) -> PyTgCalls:
        key = id(client)

        if key not in self.calls:
            self.calls[key] = PyTgCalls(client)

        return self.calls[key]

    def register_events(self, client: Client, call: PyTgCalls):
        key = id(client)

        if key in self.registered:
            return

        @call.on_stream_end()
        async def stream_end_handler(_, update):
            chat_id = update.chat_id

            try:
                await pop_current(chat_id)
                next_track = get_current_track(chat_id)

                if not next_track:
                    await self.leave(client, chat_id)
                    await clear_queue(chat_id)
                    LOGGER(__name__).info(
                        f"Queue finished in chat {chat_id}"
                    )
                    return

                await self.change_stream(
                    client,
                    chat_id,
                    next_track["path"],
                    video=next_track.get("stream_type") == "video",
                )

                LOGGER(__name__).info(
                    f"Auto-next started in chat {chat_id}: "
                    f"{next_track.get('title', 'Unknown')}"
                )

            except Exception as e:
                LOGGER(__name__).error(
                    f"Auto-next failed in chat {chat_id}: {e}"
                )

                try:
                    await self.leave(client, chat_id)
                    await clear_queue(chat_id)
                except Exception:
                    pass

        self.registered.add(key)

    async def start(self, clients: list):
        for client in clients:
            call = self.get_call(client)
            self.register_events(client, call)

            await call.start()

            LOGGER(__name__).info(
                f"PyTgCalls started for {client.name}"
            )

    def build_stream(self, path: str, video: bool = False):
        if video:
            return AudioVideoPiped(
                path,
                HighQualityAudio(),
                MediumQualityVideo(),
            )

        return AudioPiped(
            path,
            HighQualityAudio(),
        )

    async def join(
        self,
        client: Client,
        chat_id: int,
        path: str,
        video: bool = False,
    ):
        call = self.get_call(client)
        stream = self.build_stream(path, video)

        try:
            await call.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )

        except AlreadyJoinedError:
            await call.change_stream(chat_id, stream)

        except (NoActiveGroupCall, TelegramServerError):
            raise

    async def change_stream(
        self,
        client: Client,
        chat_id: int,
        path: str,
        video: bool = False,
    ):
        call = self.get_call(client)
        stream = self.build_stream(path, video)

        await call.change_stream(chat_id, stream)

    async def leave(self, client: Client, chat_id: int):
        call = self.get_call(client)

        try:
            await call.leave_group_call(chat_id)
        except NoActiveGroupCall:
            pass
        except Exception as e:
            LOGGER(__name__).warning(
                f"Leave call error in {chat_id}: {e}"
            )

    async def pause(self, client: Client, chat_id: int):
        await self.get_call(client).pause_stream(chat_id)

    async def resume(self, client: Client, chat_id: int):
        await self.get_call(client).resume_stream(chat_id)

    async def mute(self, client: Client, chat_id: int):
        await self.get_call(client).mute_stream(chat_id)

    async def unmute(self, client: Client, chat_id: int):
        await self.get_call(client).unmute_stream(chat_id)


Apple = AppleCall()
