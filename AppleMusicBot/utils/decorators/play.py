
import asyncio

from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from AppleMusicBot import YouTube, app
from AppleMusicBot.misc import SUDOERS
from AppleMusicBot.utils.database import (
    get_assistant,
    get_cmode,
    get_lang,
    get_playmode,
    get_playtype,
    is_active_chat,
    is_maintenance,
)
from AppleMusicBot.utils.inline import botplaylist_markup
from config import PLAYLIST_IMG_URL, SUPPORT_CHAT, adminlist
from strings import get_string

links = {}


def PlayWrapper(command):
    async def wrapper(client, message):
        language = await get_lang(message.chat.id)
        _ = get_string(language)

        # Anonymous admin protection
        if message.sender_chat:
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ʜᴏᴡ ᴛᴏ ғɪx ?",
                            callback_data="AnonymousAdmin",
                        ),
                    ]
                ]
            )
            return await message.reply_text(
                _["general_3"],
                reply_markup=upl,
            )

        # Maintenance check (FIXED)
        if await is_maintenance() is True:
            if message.from_user.id not in SUDOERS:
                return await message.reply_text(
                    text=(
                        f"{app.mention} is under maintenance. "
                        f"Visit <a href={SUPPORT_CHAT}>support chat</a> "
                        "for details."
                    ),
                    disable_web_page_preview=True,
                )

        # Delete command message
        try:
            await message.delete()
        except Exception:
            pass

        # Check replied Telegram audio/video
        audio_telegram = (
            (
                message.reply_to_message.audio
                or message.reply_to_message.voice
            )
            if message.reply_to_message
            else None
        )

        video_telegram = (
            (
                message.reply_to_message.video
                or message.reply_to_message.document
            )
            if message.reply_to_message
            else None
        )

        # Extract YouTube URL
        url = await YouTube.url(message)

        # Empty command handling
        if (
            audio_telegram is None
            and video_telegram is None
            and url is None
        ):
            if len(message.command) < 2:
                if "stream" in message.command:
                    return await message.reply_text(_["str_1"])

                buttons = botplaylist_markup(_)

                return await message.reply_photo(
                    photo=PLAYLIST_IMG_URL,
                    caption=_["play_18"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )

        # Channel play mode
        if message.command[0][0] == "c":
            chat_id = await get_cmode(message.chat.id)

            if chat_id is None:
                return await message.reply_text(_["setting_7"])

            try:
                chat = await app.get_chat(chat_id)
            except Exception:
                return await message.reply_text(_["cplay_4"])

            channel = chat.title

        else:
            chat_id = message.chat.id
            channel = None

        # Get play settings
        playmode = await get_playmode(message.chat.id)
        playty = await get_playtype(message.chat.id)

        # Admin-only playback check
        if playty != "Everyone":
            if message.from_user.id not in SUDOERS:
                admins = adminlist.get(message.chat.id)

                if not admins:
                    return await message.reply_text(_["admin_13"])

                if message.from_user.id not in admins:
                    return await message.reply_text(_["play_4"])

        # Audio / video mode
        if message.command[0][0] == "v":
            video = True
        else:
            if "-v" in message.text:
                video = True
            else:
                video = (
                    True
                    if message.command[0][1] == "v"
                    else None
                )

        # Force play mode
        if message.command[0][-1] == "e":
            if not await is_active_chat(chat_id):
                return await message.reply_text(_["play_16"])

            fplay = True
        else:
            fplay = None

        # Check assistant in voice chat
        if not await is_active_chat(chat_id):
            userbot = await get_assistant(chat_id)

            try:
                try:
                    try:
                        get = await app.get_chat_member(
                            chat_id,
                            int(userbot.id),
                        )
                    except Exception:
                        get = await app.get_chat_member(
                            chat_id,
                            userbot.username,
                        )

                except ChatAdminRequired:
                    return await message.reply_text(_["call_1"])

                if (
                    get.status == ChatMemberStatus.BANNED
                    or get.status == ChatMemberStatus.RESTRICTED
                ):
                    return await message.reply_text(
                        _["call_2"].format(
                            app.mention,
                            userbot.id,
                            userbot.name,
                            userbot.username,
                        )
                    )

            except UserNotParticipant:
                # Get group invite link
                if chat_id in links:
                    invitelink = links[chat_id]

                else:
                    if message.chat.username:
                        invitelink = message.chat.username

                        try:
                            await userbot.resolve_peer(invitelink)
                        except Exception:
                            pass

                    else:
                        try:
                            invitelink = await app.export_chat_invite_link(
                                chat_id
                            )

                        except ChatAdminRequired:
                            return await message.reply_text(_["call_1"])

                        except Exception as e:
                            return await message.reply_text(
                                _["call_3"].format(
                                    app.mention,
                                    type(e).__name__,
                                )
                            )

                # Convert invite link
                if invitelink.startswith("https://t.me/+"):
                    invitelink = invitelink.replace(
                        "https://t.me/+",
                        "https://t.me/joinchat/",
                    )

                myu = await message.reply_text(
                    _["call_4"].format(app.mention)
                )

                try:
                    await asyncio.sleep(1)
                    await userbot.join_chat(invitelink)

                except InviteRequestSent:
                    try:
                        await app.approve_chat_join_request(
                            chat_id,
                            userbot.id,
                        )

                    except Exception as e:
                        return await message.reply_text(
                            _["call_3"].format(
                                app.mention,
                                type(e).__name__,
                            )
                        )

                    await asyncio.sleep(3)
                    await myu.edit(
                        _["call_5"].format(app.mention)
                    )

                except UserAlreadyParticipant:
                    pass

                except Exception as e:
                    return await message.reply_text(
                        _["call_3"].format(
                            app.mention,
                            type(e).__name__,
                        )
                    )

                links[chat_id] = invitelink

                try:
                    await userbot.resolve_peer(chat_id)
                except Exception:
                    pass

        # Execute original play command
        return await command(
            client,
            message,
            _,
            chat_id,
            video,
            channel,
            playmode,
            url,
            fplay,
        )

    return wrapper
