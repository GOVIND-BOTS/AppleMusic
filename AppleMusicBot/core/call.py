
import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import (
    HighQualityAudio,
    MediumQualityVideo,
)
from pytgcalls.types.stream import StreamAudioEnded

import config
from AppleMusicBot import LOGGER, YouTube, app
from AppleMusicBot.misc import db
from AppleMusicBot.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from AppleMusicBot.utils.exceptions import AssistantErr
from AppleMusicBot.utils.formatters import (
    check_duration,
    seconds_to_min,
    speed_converter,
)
from AppleMusicBot.utils.inline.play import stream_markup
from AppleMusicBot.utils.stream.autoclear import auto_clean
from AppleMusicBot.utils.thumbnails import get_thumb
from strings import get_string


autoend = {}
counter = {}


async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


class Call:
    def __init__(self):
        def make_call_client(name, session):
            if not session or not str(session).strip():
                return None, None

            user_client = Client(
                name=name,
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(session).strip(),
            )
            return user_client, PyTgCalls(user_client, cache_duration=100)

        self.userbot1, self.one = make_call_client("AnonXAss1", config.STRING1)
        self.userbot2, self.two = make_call_client("AnonXAss2", config.STRING2)
        self.userbot3, self.three = make_call_client("AnonXAss3", config.STRING3)
        self.userbot4, self.four = make_call_client("AnonXAss4", config.STRING4)
        self.userbot5, self.five = make_call_client("AnonXAss5", config.STRING5)

        self.clients = [
            (config.STRING1, self.one),
            (config.STRING2, self.two),
            (config.STRING3, self.three),
            (config.STRING4, self.four),
            (config.STRING5, self.five),
        ]

        self.started_clients = []
        self._handlers_registered = False

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)

        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except Exception:
            pass

    async def stop_stream_force(self, chat_id: int):
        for session, client in self.clients:
            if not session:
                continue

            try:
                await client.leave_group_call(chat_id)
            except Exception:
                pass

        try:
            await _clear_(chat_id)
        except Exception:
            pass

    async def speedup_stream(
        self,
        chat_id: int,
        file_path,
        speed,
        playing,
    ):
        assistant = await group_assistant(self, chat_id)

        if str(speed) != "1.0":
            base = os.path.basename(file_path)
            chatdir = os.path.join(
                os.getcwd(),
                "playback",
                str(speed),
            )

            os.makedirs(chatdir, exist_ok=True)
            out = os.path.join(chatdir, base)

            if not os.path.isfile(out):
                speed_values = {
                    "0.5": 2.0,
                    "0.75": 1.35,
                    "1.5": 0.68,
                    "2.0": 0.5,
                }

                vs = speed_values.get(str(speed))

                if vs is None:
                    raise AssistantErr("Unsupported playback speed.")

                proc = await asyncio.create_subprocess_exec(
                    "ffmpeg",
                    "-y",
                    "-i",
                    file_path,
                    "-filter:v",
                    f"setpts={vs}*PTS",
                    "-filter:a",
                    f"atempo={speed}",
                    out,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                _, stderr = await proc.communicate()

                if proc.returncode != 0:
                    raise AssistantErr(
                        stderr.decode(errors="ignore")[-1000:]
                    )
        else:
            out = file_path

        loop = asyncio.get_running_loop()
        dur = await loop.run_in_executor(
            None,
            check_duration,
            out,
        )
        dur = int(dur)

        played, con_seconds = speed_converter(
            playing[0]["played"],
            speed,
        )
        duration = seconds_to_min(dur)

        if playing[0]["streamtype"] == "video":
            stream = AudioVideoPiped(
                out,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=(
                    f"-ss {played} -to {duration}"
                ),
            )
        else:
            stream = AudioPiped(
                out,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=(
                    f"-ss {played} -to {duration}"
                ),
            )

        if str(db[chat_id][0]["file"]) != str(file_path):
            raise AssistantErr("Umm")

        await assistant.change_stream(chat_id, stream)

        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = playing[0].get("old_dur")

            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]

            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)

        try:
            check = db.get(chat_id)
            if check:
                check.pop(0)
        except Exception:
            pass

        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)

        try:
            await assistant.leave_group_call(chat_id)
        except Exception:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)

        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = AudioPiped(
                link,
                audio_parameters=HighQualityAudio(),
            )

        await assistant.change_stream(chat_id, stream)

    async def seek_stream(
        self,
        chat_id,
        file_path,
        to_seek,
        duration,
        mode,
    ):
        assistant = await group_assistant(self, chat_id)

        if mode == "video":
            stream = AudioVideoPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=(
                    f"-ss {to_seek} -to {duration}"
                ),
            )
        else:
            stream = AudioPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=(
                    f"-ss {to_seek} -to {duration}"
                ),
            )

        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        if not config.LOGGER_ID:
            raise AssistantErr("LOGGER_ID is not configured.")

        assistant = await group_assistant(self, config.LOGGER_ID)

        await assistant.join_group_call(
            config.LOGGER_ID,
            AudioVideoPiped(link),
            stream_type=StreamType().pulse_stream,
        )

        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOGGER_ID)

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)

        language = await get_lang(chat_id)
        _ = get_string(language)

        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = AudioPiped(
                link,
                audio_parameters=HighQualityAudio(),
            )

        try:
            await assistant.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )

        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])

        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])

        except TelegramServerError:
            raise AssistantErr(_["call_10"])

        await add_active_chat(chat_id)
        await music_on(chat_id)

        if video:
            await add_active_video_chat(chat_id)

        if await is_autoend():
            counter[chat_id] = {}

            users = len(
                await assistant.get_participants(chat_id)
            )

            if users == 1:
                autoend[chat_id] = (
                    datetime.now() + timedelta(minutes=1)
                )

    async def change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)

        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop -= 1
                await set_loop(chat_id, loop)

            if popped:
                await auto_clean(popped)

            if not check:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)

        except Exception:
            try:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            except Exception:
                return

        queued = check[0]["file"]
        language = await get_lang(chat_id)
        _ = get_string(language)

        title = check[0]["title"].title()
        user = check[0]["by"]
        user_id = check[0]["user_id"]
        original_chat_id = check[0]["chat_id"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]

        db[chat_id][0]["played"] = 0

        exis = check[0].get("old_dur")

        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0

        video = str(streamtype) == "video"

        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)

            if n == 0:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            if video:
                stream = AudioVideoPiped(
                    link,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
            else:
                stream = AudioPiped(
                    link,
                    audio_parameters=HighQualityAudio(),
                )

            try:
                await client.change_stream(chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            img = await get_thumb(videoid, user_id)
            button = stream_markup(_, chat_id)

            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

        elif "vid_" in queued:
            mystic = await app.send_message(
                original_chat_id,
                _["call_7"],
            )

            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=video,
                )
            except Exception:
                return await mystic.edit_text(
                    _["call_6"],
                    disable_web_page_preview=True,
                )

            if video:
                stream = AudioVideoPiped(
                    file_path,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
            else:
                stream = AudioPiped(
                    file_path,
                    audio_parameters=HighQualityAudio(),
                )

            try:
                await client.change_stream(chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            img = await get_thumb(videoid, user_id)
            button = stream_markup(_, chat_id)

            await mystic.delete()

            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

        elif "index_" in queued:
            if video:
                stream = AudioVideoPiped(
                    videoid,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
            else:
                stream = AudioPiped(
                    videoid,
                    audio_parameters=HighQualityAudio(),
                )

            try:
                await client.change_stream(chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            button = stream_markup(_, chat_id)

            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user),
                reply_markup=InlineKeyboardMarkup(button),
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

        else:
            if video:
                stream = AudioVideoPiped(
                    queued,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
            else:
                stream = AudioPiped(
                    queued,
                    audio_parameters=HighQualityAudio(),
                )

            try:
                await client.change_stream(chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            button = stream_markup(_, chat_id)

            if videoid == "telegram":
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=(
                        config.TELEGRAM_AUDIO_URL
                        if str(streamtype) == "audio"
                        else config.TELEGRAM_VIDEO_URL
                    ),
                    caption=_["stream_1"].format(
                        config.SUPPORT_CHAT,
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )

                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            elif videoid == "soundcloud":
                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=config.SOUNCLOUD_IMG_URL,
                    caption=_["stream_1"].format(
                        config.SUPPORT_CHAT,
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )

                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            else:
                img = await get_thumb(videoid, user_id)

                run = await app.send_photo(
                    chat_id=original_chat_id,
                    photo=img,
                    caption=_["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(button),
                )

                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

    async def ping(self):
        pings = []

        for session, client in self.clients:
            if not session:
                continue

            try:
                value = client.ping
                if callable(value):
                    value = value()

                if asyncio.iscoroutine(value):
                    value = await value

                pings.append(value)

            except Exception:
                continue

        if not pings:
            return "0"

        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls clients...")

        if not self._handlers_registered:
            await self.decorators()
            self._handlers_registered = True

        try:
            for session, client in self.clients:
                if session:
                    await client.start()
                    self.started_clients.append(client)

            LOGGER(__name__).info(
                f"Started {len(self.started_clients)} assistant clients."
            )

        except Exception:
            LOGGER(__name__).exception(
                "PyTgCalls startup failed."
            )
            await self.stop()
            raise

    async def stop(self):
        LOGGER(__name__).info(
            "Stopping active voice chats and assistant clients..."
        )

        # Leave active voice chats before shutting down clients.
        for session, client in self.clients:
            if not session:
                continue

            try:
                calls = await client.calls

                for chat_id in list(calls.keys()):
                    try:
                        await client.leave_group_call(chat_id)
                    except Exception:
                        pass

            except Exception:
                pass

        # Stop only when the installed PyTgCalls version exposes stop().
        for client in reversed(self.started_clients):
            stop_method = getattr(client, "stop", None)

            if callable(stop_method):
                try:
                    result = stop_method()

                    if asyncio.iscoroutine(result):
                        await result

                except Exception as e:
                    LOGGER(__name__).warning(
                        f"PyTgCalls stop warning: {type(e).__name__}: {e}"
                    )

        self.started_clients.clear()

        LOGGER(__name__).info(
            "Assistant shutdown sequence completed."
        )

    async def decorators(self):
        clients = [
            client
            for session, client in self.clients
            if session
        ]

        if not clients:
            return

        def register_events(event_name, handler):
            for client in clients:
                decorator = getattr(client, event_name)()
                decorator(handler)

        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        async def stream_end_handler(client, update: Update):
            if not isinstance(update, StreamAudioEnded):
                return

            await self.change_stream(
                client,
                update.chat_id,
            )

        for event_name in (
            "on_kicked",
            "on_closed_voice_chat",
            "on_left",
        ):
            register_events(
                event_name,
                stream_services_handler,
            )

        register_events(
            "on_stream_end",
            stream_end_handler,
        )


AppleBot = Call()
