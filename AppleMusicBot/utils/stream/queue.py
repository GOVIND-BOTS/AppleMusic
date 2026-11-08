
import asyncio

from AppleMusicBot.misc import db

_queue_locks = {}


def get_queue_lock(chat_id: int):
    if chat_id not in _queue_locks:
        _queue_locks[chat_id] = asyncio.Lock()
    return _queue_locks[chat_id]


async def put_queue(
    chat_id: int,
    title: str,
    duration: str,
    path: str,
    user: str,
    stream_type: str = "audio",
    videoid: str = "",
    **kwargs,
):
    track = {
        "title": title,
        "duration": duration,
        "path": path,
        "user": user,
        "stream_type": stream_type,
        "videoid": videoid,
    }

    async with get_queue_lock(chat_id):
        if chat_id not in db:
            db[chat_id] = []

        db[chat_id].append(track)
        return len(db[chat_id]) - 1


async def clear_queue(chat_id: int):
    async with get_queue_lock(chat_id):
        db[chat_id] = []


def get_queue(chat_id: int):
    return db.get(chat_id, [])


def get_current_track(chat_id: int):
    queue = db.get(chat_id, [])
    return queue[0] if queue else None


async def pop_current(chat_id: int):
    async with get_queue_lock(chat_id):
        queue = db.get(chat_id, [])

        if not queue:
            return None

        return queue.pop(0)


async def get_next_track(chat_id: int):
    async with get_queue_lock(chat_id):
        queue = db.get(chat_id, [])

        if len(queue) < 2:
            return None

        return queue[1]


async def remove_track(chat_id: int, index: int):
    async with get_queue_lock(chat_id):
        queue = db.get(chat_id, [])

        if index < 0 or index >= len(queue):
            return None

        return queue.pop(index)


async def remove_last_queue(chat_id: int):
    async with get_queue_lock(chat_id):
        queue = db.get(chat_id, [])

        if not queue:
            return None

        return queue.pop()


async def replace_current(chat_id: int, track: dict):
    async with get_queue_lock(chat_id):
        if chat_id not in db:
            db[chat_id] = []

        if db[chat_id]:
            db[chat_id][0] = track
        else:
            db[chat_id].append(track)

        return track


def queue_length(chat_id: int):
    return len(db.get(chat_id, []))
