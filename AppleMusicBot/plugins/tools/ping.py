from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message

from AppleMusicBot import app
from AppleMusicBot.core.call import AppleBot
from AppleMusicBot.utils.sys import bot_sys_stats
from AppleMusicBot.utils.decorators.language import LanguageStart
from AppleMusicBot.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL


@app.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@LanguageStart
async def ping_com(client, message: Message, _):
    started_at = datetime.now()

    response = await message.reply_photo(
        photo=PING_IMG_URL,
        caption=_["ping_1"].format(app.mention),
    )

    # PyTgCalls ping is optional: report N/A instead of breaking /ping
    # when the installed PyTgCalls build does not expose a ping value.
    try:
        pytgping = await AppleBot.ping()
    except Exception:
        pytgping = "N/A"

    try:
        UP, CPU, RAM, DISK = await bot_sys_stats()
    except Exception:
        UP, CPU, RAM, DISK = "N/A", "N/A", "N/A", "N/A"

    # Include whole seconds as well as microseconds for accurate latency.
    resp = (datetime.now() - started_at).total_seconds() * 1000

    # A photo message must be edited through its caption, not edit_text().
    await response.edit_caption(
        caption=_["ping_2"].format(
            round(resp, 2),
            app.mention,
            UP,
            RAM,
            CPU,
            DISK,
            pytgping,
        ),
        reply_markup=supp_markup(_),
    )
