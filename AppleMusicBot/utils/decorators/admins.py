from functools import wraps

from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message

from config import OWNER_ID
from AppleMusic import app


def AdminRightsCheck(mystic):
    @wraps(mystic)
    async def wrapper(client, message: Message, *args, **kwargs):
        if not message.from_user:
            return
        if message.from_user.id == OWNER_ID:
            return await mystic(client, message, *args, **kwargs)
        try:
            member = await app.get_chat_member(
                message.chat.id,
                message.from_user.id,
            )
            if member.status in (
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ):
                return await mystic(client, message, *args, **kwargs)
        except Exception:
            pass
        return await message.reply_text("Sirf admins ye command use kar sakte hain.")
    return wrapper
