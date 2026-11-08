from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from AppleMusic import app
from config import BANNED_USERS


@app.on_message(filters.command(["start", "help"]) & filters.private & ~BANNED_USERS)
async def start_private(_, message: Message):
    await message.reply_photo(
        photo=config.START_IMG_URL,
        caption=(
            f"**🍎 {config.BOT_NAME}**\n\n"
            "Superfast multi-platform Telegram music bot.\n\n"
            "**Platforms**\n"
            "• YouTube • Spotify • Apple Music\n"
            "• SoundCloud • Resso • Telegram files\n\n"
            "**Commands**\n"
            "`/play` `/vplay` `/pause` `/resume`\n"
            "`/skip` `/stop` `/queue` `/ping`\n\n"
            "Add me to your group and enjoy music."
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "➕ Add to Group",
                        url=f"https://t.me/{app.username}?startgroup=true",
                    )
                ],
                [
                    InlineKeyboardButton("Support", url=config.SUPPORT_CHAT),
                    InlineKeyboardButton("Channel", url=config.SUPPORT_CHANNEL),
                ],
            ]
        ),
    )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
async def start_group(_, message: Message):
    await message.reply_text(
        f"**{config.BOT_NAME}** is online.\nUse `/play song name` to start."
    )
