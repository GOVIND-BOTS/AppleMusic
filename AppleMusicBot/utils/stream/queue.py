from AppleMusic.misc import db


async def put_queue(
    chat_id: int,
    title: str,
    duration: str,
    path: str,
    user: str,
    stream_type: str = "audio",
    videoid: str = "",
):
    if chat_id not in db:
        db[chat_id] = []
    db[chat_id].append(
        {
            "title": title,
            "duration": duration,
            "path": path,
            "user": user,
            "stream_type": stream_type,
            "videoid": videoid,
        }
    )
    return len(db[chat_id]) - 1


async def clear_queue(chat_id: int):
    db[chat_id] = []


def get_queue(chat_id: int):
    return db.get(chat_id, [])
