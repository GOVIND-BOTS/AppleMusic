
from typing import Union

from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, Message

from AppleMusicBot import app
from AppleMusicBot.utils.inline.help import (
    help_pannel,
    help_back_markup,
    private_help_panel,
)
from AppleMusicBot.utils.database import get_lang
from AppleMusicBot.utils.decorators.language import LanguageStart, languageCB
from config import BANNED_USERS, START_IMG_URL, SUPPORT_CHAT
from strings import get_string, helpers


@app.on_message(filters.command(["help"]) & filters.private & ~BANNED_USERS)
@app.on_callback_query(filters.regex("settings_back_helper") & ~BANNED_USERS)
async def helper_private(
    client: app, update: Union[types.Message, types.CallbackQuery]
):
    is_callback = isinstance(update, types.CallbackQuery)

    if is_callback:
        try:
            await update.answer()
        except Exception:
            pass

        if not update.message:
            return

        chat_id = update.message.chat.id
        language = await get_lang(chat_id)
        _ = get_string(language)
        keyboard = help_pannel(_, True)

        await update.edit_message_text(
            _["help_1"].format(SUPPORT_CHAT),
            reply_markup=keyboard,
        )
        return

    try:
        await update.delete()
    except Exception:
        pass

    language = await get_lang(update.chat.id)
    _ = get_string(language)
    keyboard = help_pannel(_)

    caption = _["help_1"].format(SUPPORT_CHAT)

    # Try sending the configured image first.
    if isinstance(START_IMG_URL, str) and START_IMG_URL.strip():
        try:
            await update.reply_photo(
                photo=START_IMG_URL.strip(),
                caption=caption,
                reply_markup=keyboard,
            )
            return
        except Exception:
            pass

    # Fallback: send help as text if image is invalid.
    await update.reply_text(
        caption,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


@app.on_message(filters.command(["help"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):
    keyboard = private_help_panel(_)
    await message.reply_text(
        _["help_2"],
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


@app.on_callback_query(filters.regex(r"^help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except Exception:
        pass

    callback_data = CallbackQuery.data.strip()

    parts = callback_data.split(None, 1)
    if len(parts) < 2:
        return

    cb = parts[1]
    keyboard = help_back_markup(_)

    help_pages = {
        "hb1": helpers.HELP_1,
        "hb2": helpers.HELP_2,
        "hb3": helpers.HELP_3,
        "hb4": helpers.HELP_4,
        "hb5": helpers.HELP_5,
        "hb6": helpers.HELP_6,
        "hb7": helpers.HELP_7,
        "hb8": helpers.HELP_8,
        "hb9": helpers.HELP_9,
        "hb10": helpers.HELP_10,
        "hb11": helpers.HELP_11,
        "hb12": helpers.HELP_12,
        "hb13": helpers.HELP_13,
        "hb14": helpers.HELP_14,
        "hb15": helpers.HELP_15,
        "hb16": helpers.HELP_16,
    }

    help_text = help_pages.get(cb)
    if help_text is None:
        await CallbackQuery.answer("Help page not found.", show_alert=True)
        return

    await CallbackQuery.edit_message_text(
        help_text,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )
