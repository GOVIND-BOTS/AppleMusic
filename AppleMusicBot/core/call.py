import asyncio
from typing import Union

from pyrogram import Client
from pyrogram.types import Message
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

from AppleMusic.logging import LOGGER
from AppleMusic.misc import db


class AppleCall:
    def __init__(self):
        self.calls = {}

    def get_call(self, client: Client) -> PyTgCalls:
        key = id(client)
        if key not in self.calls:
            self.calls[key] = PyTgCalls(client)
        return self.calls[key]

    async def start(self, clients: list):
        for client in clients:
            call = self.get_call(client)
            await call.start()
            LOGGER(__name__).info(f"PyTgCalls started for {client.name}")

    async def join(
        self,
        client: Client,
        chat_id: int,
        path: str,
        video: bool = False,
    ):
        call = self.get_call(client)
        stream = (
            AudioVideoPiped(
                path,
                HighQualityAudio(),
                MediumQualityVideo(),
            )
            if video
            else AudioPiped(path, HighQualityAudio())
        )
        try:
            await call.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )
        except AlreadyJoinedError:
            await call.change_stream(chat_id, stream)
        except NoActiveGroupCall:
            raise
        except TelegramServerError:
            raise

    async def change_stream(self, client: Client, chat_id: int, path: str, video: bool = False):
        call = self.get_call(client)
        stream = (
            AudioVideoPiped(path, HighQualityAudio(), MediumQualityVideo())
            if video
            else AudioPiped(path, HighQualityAudio())
        )
        await call.change_stream(chat_id, stream)

    async def leave(self, client: Client, chat_id: int):
        call = self.get_call(client)
        try:
            await call.leave_group_call(chat_id)
        except Exception:
            pass

    async def pause(self, client: Client, chat_id: int):
        await self.get_call(client).pause_stream(chat_id)

    async def resume(self, client: Client, chat_id: int):
        await self.get_call(client).resume_stream(chat_id)

    async def mute(self, client: Client, chat_id: int):
        await self.get_call(client).mute_stream(chat_id)

    async def unmute(self, client: Client, chat_id: int):
        await self.get_call(client).unmute_stream(chat_id)


Apple = AppleCall()
