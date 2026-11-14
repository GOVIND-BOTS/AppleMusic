import asyncio
import os
import shutil
from datetime import datetime

import urllib3
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from pyrogram import filters

import config
from AppleMusicBot import app, misc
from AppleMusicBot.core.git import _authenticated_git_context
from AppleMusicBot.misc import SUDOERS
from AppleMusicBot.utils.database import (
    get_active_chats,
    remove_active_chat,
    remove_active_video_chat,
)
from AppleMusicBot.utils.decorators.language import language
from AppleMusicBot.utils.pastebin import AnonyBin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


async def is_heroku():
    return misc.is_heroku()


@app.on_message(filters.command(["getlog", "logs", "getlogs"]) & SUDOERS)
@language
async def log_(client, message, _):
    try:
        await message.reply_document(document="log.txt")
    except Exception:
        await message.reply_text(_["server_1"])


@app.on_message(filters.command(["update", "gitpull"]) & SUDOERS)
@language
async def update_(client, message, _):
    on_heroku = await is_heroku()
    if on_heroku and misc.HAPP is None:
        return await message.reply_text(_["server_2"])

    response = await message.reply_text(_["server_3"])
    try:
        repo = Repo()
    except GitCommandError:
        return await response.edit(_["server_4"])
    except InvalidGitRepositoryError:
        return await response.edit(_["server_5"])

    try:
        with _authenticated_git_context(repo):
            repo.remotes.origin.fetch(config.UPSTREAM_BRANCH)
    except Exception as exc:
        return await response.edit(
            f"Git fetch failed: {type(exc).__name__}: {exc}"
        )

    verification = list(
        repo.iter_commits(f"HEAD..origin/{config.UPSTREAM_BRANCH}")
    )
    if not verification:
        return await response.edit(_["server_6"])

    repo_url = repo.remotes.origin.url.split(".git")[0]
    updates = ""
    for info in verification:
        committed = datetime.fromtimestamp(info.committed_date)
        day = committed.day
        suffix = "th" if 11 <= day % 100 <= 13 else {
            1: "st", 2: "nd", 3: "rd"
        }.get(day % 10, "th")
        updates += (
            f"<b>➣ #{info.count()}: "
            f"<a href={repo_url}/commit/{info}>{info.summary}</a> "
            f"ʙʏ -> {info.author}</b>\n"
            f"<b>➥ ᴄᴏᴍᴍɪᴛᴇᴅ ᴏɴ :</b> "
            f"{day}{suffix} {committed.strftime('%b, %Y')}\n\n"
        )

    header = (
        "<b>ᴀ ɴᴇᴡ ᴜᴩᴅᴀᴛᴇ ɪs ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛʜᴇ ʙᴏᴛ !</b>\n\n"
        "➣ ᴩᴜsʜɪɴɢ ᴜᴩᴅᴀᴛᴇs ɴᴏᴡ\n\n"
        "<b><u>ᴜᴩᴅᴀᴛᴇs:</u></b>\n\n"
    )
    final_text = header + updates
    if len(final_text) > 4096:
        url = await AnonyBin(updates)
        nrs = await response.edit(
            f"{header}<a href={url}>ᴄʜᴇᴄᴋ ᴜᴩᴅᴀᴛᴇs</a>"
        )
    else:
        nrs = await response.edit(
            final_text, disable_web_page_preview=True
        )

    try:
        repo.git.stash("push", "--include-untracked")
        with _authenticated_git_context(repo):
            repo.remotes.origin.pull(config.UPSTREAM_BRANCH)
    except Exception as exc:
        return await response.edit(
            f"Update failed: {type(exc).__name__}: {exc}"
        )

    try:
        served_chats = await get_active_chats()
        for chat_id in list(served_chats):
            try:
                await app.send_message(
                    chat_id=int(chat_id),
                    text=_[ "server_8" ].format(app.mention),
                )
                await remove_active_chat(chat_id)
                await remove_active_video_chat(chat_id)
            except Exception:
                pass
        await response.edit(f"{nrs.text}\n\n{_['server_7']}")
    except Exception:
        pass

    if on_heroku:
        try:
            await asyncio.to_thread(misc.HAPP.restart)
            return
        except Exception as exc:
            return await response.edit(
                f"{nrs.text}\n\nHeroku restart failed: "
                f"{type(exc).__name__}: {exc}"
            )

    os.system("pip install -r requirements.txt")
    os.execlp("bash", "bash", "start")


@app.on_message(filters.command(["restart"]) & SUDOERS)
async def restart_(_, message):
    response = await message.reply_text("ʀᴇsᴛᴀʀᴛɪɴɢ...")
    for chat_id in list(await get_active_chats()):
        try:
            await app.send_message(
                chat_id=int(chat_id),
                text=(
                    f"{app.mention} ɪs ʀᴇsᴛᴀʀᴛɪɴɢ...\n\n"
                    "ʏᴏᴜ ᴄᴀɴ sᴛᴀʀᴛ ᴩʟᴀʏɪɴɢ ᴀɢᴀɪɴ ᴀғᴛᴇʀ 15-20 sᴇᴄᴏɴᴅs."
                ),
            )
            await remove_active_chat(chat_id)
            await remove_active_video_chat(chat_id)
        except Exception:
            pass

    for folder in ("downloads", "raw_files", "cache"):
        try:
            shutil.rmtree(folder)
        except FileNotFoundError:
            pass
        except Exception:
            pass

    await response.edit_text(
        "» ʀᴇsᴛᴀʀᴛ ᴘʀᴏᴄᴇss sᴛᴀʀᴛᴇᴅ, ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ғᴏʀ ғᴇᴡ sᴇᴄᴏɴᴅs..."
    )
    os.execlp("bash", "bash", "start")
