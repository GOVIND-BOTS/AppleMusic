
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def editor_menu(
    effect="cinematic",
    duration=10,
    media_type="video",
    start_time=0,
):
    if media_type == "photo":
        timing_title = "📸 Photo Duration"
        effects = [
            [
                InlineKeyboardButton("❤️ Romantic", callback_data="ac:effect:romantic"),
                InlineKeyboardButton("💔 Sad", callback_data="ac:effect:sad"),
            ],
            [
                InlineKeyboardButton("🥺 Memories", callback_data="ac:effect:memories"),
                InlineKeyboardButton("🔥 Attitude", callback_data="ac:effect:attitude"),
            ],
            [
                InlineKeyboardButton("🎬 Cinematic", callback_data="ac:effect:cinematic"),
                InlineKeyboardButton("🖤 B&W", callback_data="ac:effect:gray"),
            ],
        ]
    else:
        timing_title = "🎬 Video Clip Length"
        effects = [
            [
                InlineKeyboardButton("🎬 Cinematic", callback_data="ac:effect:cinematic"),
                InlineKeyboardButton("⚡ Glitch", callback_data="ac:effect:glitch"),
            ],
            [
                InlineKeyboardButton("📳 Shake", callback_data="ac:effect:shake"),
                InlineKeyboardButton("🌈 RGB", callback_data="ac:effect:rgb"),
            ],
            [
                InlineKeyboardButton("🖤 B&W", callback_data="ac:effect:gray"),
                InlineKeyboardButton("📼 Vintage", callback_data="ac:effect:vintage"),
            ],
            [
                InlineKeyboardButton("🌫 Blur", callback_data="ac:effect:blur"),
                InlineKeyboardButton("🐢 Slow", callback_data="ac:effect:slow"),
                InlineKeyboardButton("⚡ Fast", callback_data="ac:effect:fast"),
            ],
        ]

    duration_buttons = [
        InlineKeyboardButton(
            f"{seconds}s" + (" ✓" if duration == seconds else ""),
            callback_data=f"ac:duration:{seconds}",
        )
        for seconds in (5, 10, 15, 30, 45, 60)
    ]

    keyboard = [
        *effects,
        [InlineKeyboardButton(timing_title, callback_data="ac:duration:info")],
        duration_buttons,
    ]

    if media_type == "video":
        keyboard.append([
            InlineKeyboardButton(
                f"⏱ Start: {start_time}s",
                callback_data="ac:start",
            )
        ])

    keyboard.extend([
        [
            InlineKeyboardButton("🎵 Replace Music", callback_data="ac:music"),
        ],
        [
            InlineKeyboardButton("🎥 Render 4K", callback_data="ac:render"),
            InlineKeyboardButton("❌ Cancel", callback_data="ac:cancel"),
        ],
    ])

    return InlineKeyboardMarkup(keyboard)


def music_cancel():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("↩️ Back", callback_data="ac:back"),
            InlineKeyboardButton("❌ Cancel", callback_data="ac:cancel"),
        ]
    ])
