from functools import wraps

from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message

from AppleMusicBot import app


def PlayWrapper(mystic):
    @wraps(mystic)
    async def wrapper(client, message: Message, *args, **kwargs):
        if message.chat.type.name == "PRIVATE":
            return await message.reply_text(
                "Ye command groups me use karo."
            )
        try:
            bot_member = await app.get_chat_member(message.chat.id, app.id)
            if bot_member.status not in (
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ):
                return await message.reply_text(
                    "Mujhe admin banao (voice chat manage permission ke sath)."
                )
        except Exception:
            pass
        return await mystic(client, message, *args, **kwargs)
    return wrapper
