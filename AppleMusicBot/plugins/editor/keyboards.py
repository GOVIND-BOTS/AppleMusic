
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def editor_menu(effect="normal", music=False):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✨ Auto Edit", callback_data="ac:effect:cinematic"),
            InlineKeyboardButton("🎬 Cinematic", callback_data="ac:effect:cinematic"),
        ],
        [
            InlineKeyboardButton("⚡ Glitch", callback_data="ac:effect:glitch"),
            InlineKeyboardButton("📳 Shake", callback_data="ac:effect:shake"),
        ],
        [
            InlineKeyboardButton("🌈 RGB", callback_data="ac:effect:rgb"),
            InlineKeyboardButton("🖤 B&W", callback_data="ac:effect:gray"),
        ],
        [
            InlineKeyboardButton("🌅 Vintage", callback_data="ac:effect:vintage"),
            InlineKeyboardButton("🔍 Blur", callback_data="ac:effect:blur"),
        ],
        [
            InlineKeyboardButton("🐢 Slow Motion", callback_data="ac:effect:slow"),
            InlineKeyboardButton("🚀 Fast Motion", callback_data="ac:effect:fast"),
        ],
        [
            InlineKeyboardButton(
                "🎵 Replace Music",
                callback_data="ac:music",
            ),
        ],
        [
            InlineKeyboardButton(
                "🎨 Render 4K Video",
                callback_data="ac:render",
            ),
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="ac:cancel"),
        ],
    ])


def music_cancel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Back", callback_data="ac:back")],
        [InlineKeyboardButton("❌ Cancel", callback_data="ac:cancel")],
    ])
