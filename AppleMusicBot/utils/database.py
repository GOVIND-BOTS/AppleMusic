
import random
from typing import Dict, List, Union

from AppleMusicBot import userbot
from AppleMusicBot.core.userbot import assistants
from AppleMusicBot.core.mongo import mongodb


authdb = mongodb.adminauth
authuserdb = mongodb.authuser
autoenddb = mongodb.autoend
assdb = mongodb.assistants
blacklist_chatdb = mongodb.blacklistChat
blockeddb = mongodb.blockedusers
chatsdb = mongodb.chats
channeldb = mongodb.cplaymode
countdb = mongodb.upcount
gbansdb = mongodb.gban
langdb = mongodb.language
onoffdb = mongodb.onoffper
playmodedb = mongodb.playmode
playtypedb = mongodb.playtypedb
skipdb = mongodb.skipmode
sudoersdb = mongodb.sudoers
usersdb = mongodb.tgusersdb


# Memory cache
active = []
activevideo = []
assistantdict = {}
autoend = {}
count = {}
channelconnect = {}
langm = {}
loop = {}
maintenance = []
nonadmin = {}
pause = {}
playmode = {}
playtype = {}
skipmode = {}


# --------------------------------------------------
# ASSISTANT SYSTEM
# --------------------------------------------------

async def get_assistant_number(chat_id: int) -> str:
    return assistantdict.get(chat_id)


async def get_client(assistant: int):
    assistant = int(assistant)

    clients = {
        1: userbot.one,
        2: userbot.two,
        3: userbot.three,
        4: userbot.four,
        5: userbot.five,
    }

    client = clients.get(assistant)

    if client is None:
        raise ValueError(f"Invalid assistant number: {assistant}")

    return client


async def set_assistant_new(chat_id: int, number: int):
    number = int(number)

    if number not in assistants:
        raise ValueError(f"Assistant {number} is not available")

    assistantdict[chat_id] = number

    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": number}},
        upsert=True,
    )


async def set_assistant(chat_id: int):
    if not assistants:
        raise RuntimeError("No assistants are configured")

    ran_assistant = random.choice(assistants)

    assistantdict[chat_id] = ran_assistant

    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": ran_assistant}},
        upsert=True,
    )

    return await get_client(ran_assistant)


async def get_assistant(chat_id: int):
    assistant = assistantdict.get(chat_id)

    if assistant is None:
        dbassistant = await assdb.find_one({"chat_id": chat_id})

        if not dbassistant:
            return await set_assistant(chat_id)

        got_assis = dbassistant.get("assistant")

        if got_assis not in assistants:
            return await set_assistant(chat_id)

        assistantdict[chat_id] = got_assis
        return await get_client(got_assis)

    if assistant not in assistants:
        return await set_assistant(chat_id)

    return await get_client(assistant)


async def set_calls_assistant(chat_id: int):
    if not assistants:
        raise RuntimeError("No assistants are configured")

    ran_assistant = random.choice(assistants)

    assistantdict[chat_id] = ran_assistant

    await assdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"assistant": ran_assistant}},
        upsert=True,
    )

    return ran_assistant


async def group_assistant(self, chat_id: int):
    # Correct package path: AppleMusicBot, not AppleMusic
    assistant = assistantdict.get(chat_id)

    if assistant is None:
        dbassistant = await assdb.find_one({"chat_id": chat_id})

        if not dbassistant:
            assis = await set_calls_assistant(chat_id)
        else:
            assis = dbassistant.get("assistant")

            if assis in assistants:
                assistantdict[chat_id] = assis
            else:
                assis = await set_calls_assistant(chat_id)

    elif assistant in assistants:
        assis = assistant
    else:
        assis = await set_calls_assistant(chat_id)

    clients = {
        1: self.one,
        2: self.two,
        3: self.three,
        4: self.four,
        5: self.five,
    }

    client = clients.get(int(assis))

    if client is None:
        raise ValueError(f"Invalid assistant number: {assis}")

    return client


# --------------------------------------------------
# SKIP MODE
# --------------------------------------------------

async def is_skipmode(chat_id: int) -> bool:
    if chat_id in skipmode:
        return skipmode[chat_id]

    user = await skipdb.find_one({"chat_id": chat_id})

    if not user:
        skipmode[chat_id] = True
        return True

    skipmode[chat_id] = False
    return False


async def skip_on(chat_id: int):
    skipmode[chat_id] = True

    user = await skipdb.find_one({"chat_id": chat_id})

    if user:
        return await skipdb.delete_one({"chat_id": chat_id})


async def skip_off(chat_id: int):
    skipmode[chat_id] = False

    user = await skipdb.find_one({"chat_id": chat_id})

    if not user:
        return await skipdb.insert_one({"chat_id": chat_id})


# --------------------------------------------------
# UPVOTE COUNT
# --------------------------------------------------

async def get_upvote_count(chat_id: int) -> int:
    if chat_id in count:
        return count[chat_id]

    mode = await countdb.find_one({"chat_id": chat_id})

    if not mode:
        return 5

    count[chat_id] = mode["mode"]
    return mode["mode"]


async def set_upvotes(chat_id: int, mode: int):
    count[chat_id] = mode

    await countdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"mode": mode}},
        upsert=True,
    )


# --------------------------------------------------
# AUTO END
# --------------------------------------------------

async def is_autoend() -> bool:
    chat_id = 1234
    user = await autoenddb.find_one({"chat_id": chat_id})
    return bool(user)


async def autoend_on():
    chat_id = 1234

    user = await autoenddb.find_one({"chat_id": chat_id})

    if not user:
        return await autoenddb.insert_one({"chat_id": chat_id})


async def autoend_off():
    chat_id = 1234
    return await autoenddb.delete_one({"chat_id": chat_id})


# --------------------------------------------------
# LOOP
# --------------------------------------------------

async def get_loop(chat_id: int) -> int:
    return loop.get(chat_id, 0)


async def set_loop(chat_id: int, mode: int):
    loop[chat_id] = mode


# --------------------------------------------------
# CHANNEL PLAY MODE
# --------------------------------------------------

async def get_cmode(chat_id: int):
    if chat_id in channelconnect:
        return channelconnect[chat_id]

    mode = await channeldb.find_one({"chat_id": chat_id})

    if not mode:
        return None

    channelconnect[chat_id] = mode["mode"]
    return mode["mode"]


async def set_cmode(chat_id: int, mode: int):
    channelconnect[chat_id] = mode

    await channeldb.update_one(
        {"chat_id": chat_id},
        {"$set": {"mode": mode}},
        upsert=True,
    )


# --------------------------------------------------
# PLAY TYPE
# --------------------------------------------------

async def get_playtype(chat_id: int) -> str:
    if chat_id in playtype:
        return playtype[chat_id]

    mode = await playtypedb.find_one({"chat_id": chat_id})

    if not mode:
        playtype[chat_id] = "Everyone"
        return "Everyone"

    playtype[chat_id] = mode["mode"]
    return mode["mode"]


async def set_playtype(chat_id: int, mode: str):
    playtype[chat_id] = mode

    await playtypedb.update_one(
        {"chat_id": chat_id},
        {"$set": {"mode": mode}},
        upsert=True,
    )


# --------------------------------------------------
# PLAY MODE
# --------------------------------------------------

async def get_playmode(chat_id: int) -> str:
    if chat_id in playmode:
        return playmode[chat_id]

    mode = await playmodedb.find_one({"chat_id": chat_id})

    if not mode:
        playmode[chat_id] = "Direct"
        return "Direct"

    playmode[chat_id] = mode["mode"]
    return mode["mode"]


async def set_playmode(chat_id: int, mode: str):
    playmode[chat_id] = mode

    await playmodedb.update_one(
        {"chat_id": chat_id},
        {"$set": {"mode": mode}},
        upsert=True,
    )


# --------------------------------------------------
# LANGUAGE
# --------------------------------------------------

async def get_lang(chat_id: int) -> str:
    if chat_id in langm:
        return langm[chat_id]

    lang = await langdb.find_one({"chat_id": chat_id})

    if not lang:
        langm[chat_id] = "en"
        return "en"

    langm[chat_id] = lang["lang"]
    return lang["lang"]


async def set_lang(chat_id: int, lang: str):
    langm[chat_id] = lang

    await langdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"lang": lang}},
        upsert=True,
    )


# --------------------------------------------------
# MUSIC PLAYING STATUS
# --------------------------------------------------

async def is_music_playing(chat_id: int) -> bool:
    return bool(pause.get(chat_id, False))


async def music_on(chat_id: int):
    pause[chat_id] = True


async def music_off(chat_id: int):
    pause[chat_id] = False


# --------------------------------------------------
# ACTIVE AUDIO CHATS
# --------------------------------------------------

async def get_active_chats() -> list:
    return active


async def is_active_chat(chat_id: int) -> bool:
    return chat_id in active


async def add_active_chat(chat_id: int):
    if chat_id not in active:
        active.append(chat_id)


async def remove_active_chat(chat_id: int):
    if chat_id in active:
        active.remove(chat_id)


# --------------------------------------------------
# ACTIVE VIDEO CHATS
# --------------------------------------------------

async def get_active_video_chats() -> list:
    return activevideo


async def is_active_video_chat(chat_id: int) -> bool:
    return chat_id in activevideo


async def add_active_video_chat(chat_id: int):
    if chat_id not in activevideo:
        activevideo.append(chat_id)


async def remove_active_video_chat(chat_id: int):
    if chat_id in activevideo:
        activevideo.remove(chat_id)


# --------------------------------------------------
# NON-ADMIN AUTH
# --------------------------------------------------

async def check_nonadmin_chat(chat_id: int) -> bool:
    user = await authdb.find_one({"chat_id": chat_id})
    return bool(user)


async def is_nonadmin_chat(chat_id: int) -> bool:
    if chat_id in nonadmin:
        return nonadmin[chat_id]

    user = await authdb.find_one({"chat_id": chat_id})

    nonadmin[chat_id] = bool(user)
    return nonadmin[chat_id]


async def add_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = True

    is_admin = await check_nonadmin_chat(chat_id)

    if is_admin:
        return

    return await authdb.insert_one({"chat_id": chat_id})


async def remove_nonadmin_chat(chat_id: int):
    nonadmin[chat_id] = False

    is_admin = await check_nonadmin_chat(chat_id)

    if not is_admin:
        return

    return await authdb.delete_one({"chat_id": chat_id})


# --------------------------------------------------
# ON / OFF SETTINGS
# --------------------------------------------------

async def is_on_off(on_off: int) -> bool:
    onoff = await onoffdb.find_one({"on_off": on_off})
    return bool(onoff)


async def add_on(on_off: int):
    is_on = await is_on_off(on_off)

    if is_on:
        return

    return await onoffdb.insert_one({"on_off": on_off})


async def add_off(on_off: int):
    is_off = await is_on_off(on_off)

    if not is_off:
        return

    return await onoffdb.delete_one({"on_off": on_off})


# --------------------------------------------------
# MAINTENANCE
# --------------------------------------------------

async def is_maintenance():
    if not maintenance:
        get = await onoffdb.find_one({"on_off": 1})

        if not get:
            maintenance.clear()
            maintenance.append(2)
            return True

        maintenance.clear()
        maintenance.append(1)
        return False

    return 1 not in maintenance


async def maintenance_off():
    maintenance.clear()
    maintenance.append(2)

    is_off = await is_on_off(1)

    if not is_off:
        return

    return await onoffdb.delete_one({"on_off": 1})


async def maintenance_on():
    maintenance.clear()
    maintenance.append(1)

    is_on = await is_on_off(1)

    if is_on:
        return

    return await onoffdb.insert_one({"on_off": 1})


# --------------------------------------------------
# SERVED USERS
# --------------------------------------------------

async def is_served_user(user_id: int) -> bool:
    user = await usersdb.find_one({"user_id": user_id})
    return bool(user)


async def get_served_users() -> list:
    users_list = []

    async for user in usersdb.find({"user_id": {"$gt": 0}}):
        users_list.append(user)

    return users_list


async def add_served_user(user_id: int):
    if await is_served_user(user_id):
        return

    return await usersdb.insert_one({"user_id": user_id})


# --------------------------------------------------
# SERVED CHATS
# --------------------------------------------------

async def get_served_chats() -> list:
    chats_list = []

    async for chat in chatsdb.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat)

    return chats_list


async def is_served_chat(chat_id: int) -> bool:
    chat = await chatsdb.find_one({"chat_id": chat_id})
    return bool(chat)


async def add_served_chat(chat_id: int):
    if await is_served_chat(chat_id):
        return

    return await chatsdb.insert_one({"chat_id": chat_id})


# --------------------------------------------------
# BLACKLIST CHATS
# --------------------------------------------------

async def blacklisted_chats() -> list:
    chats_list = []

    async for chat in blacklist_chatdb.find({"chat_id": {"$lt": 0}}):
        chats_list.append(chat["chat_id"])

    return chats_list


async def blacklist_chat(chat_id: int) -> bool:
    if await blacklist_chatdb.find_one({"chat_id": chat_id}):
        return False

    await blacklist_chatdb.insert_one({"chat_id": chat_id})
    return True


async def whitelist_chat(chat_id: int) -> bool:
    if not await blacklist_chatdb.find_one({"chat_id": chat_id}):
        return False

    await blacklist_chatdb.delete_one({"chat_id": chat_id})
    return True


# --------------------------------------------------
# AUTH USERS / NOTES
# --------------------------------------------------

async def _get_authusers(chat_id: int) -> Dict[str, int]:
    notes = await authuserdb.find_one({"chat_id": chat_id})

    if not notes:
        return {}

    return notes.get("notes", {})


async def get_authuser_names(chat_id: int) -> List[str]:
    notes = await _get_authusers(chat_id)
    return list(notes.keys())


async def get_authuser(chat_id: int, name: str) -> Union[bool, dict]:
    notes = await _get_authusers(chat_id)
    return notes.get(name, False)


async def save_authuser(chat_id: int, name: str, note: dict):
    notes = await _get_authusers(chat_id)
    notes[name] = note

    return await authuserdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"notes": notes}},
        upsert=True,
    )


async def delete_authuser(chat_id: int, name: str) -> bool:
    notes = await _get_authusers(chat_id)

    if name not in notes:
        return False

    del notes[name]

    await authuserdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"notes": notes}},
        upsert=True,
    )

    return True


# --------------------------------------------------
# GLOBAL BAN
# --------------------------------------------------

async def get_gbanned() -> list:
    results = []

    async for user in gbansdb.find({"user_id": {"$gt": 0}}):
        results.append(user["user_id"])

    return results


async def is_gbanned_user(user_id: int) -> bool:
    user = await gbansdb.find_one({"user_id": user_id})
    return bool(user)


async def add_gban_user(user_id: int):
    if await is_gbanned_user(user_id):
        return

    return await gbansdb.insert_one({"user_id": user_id})


async def remove_gban_user(user_id: int):
    if not await is_gbanned_user(user_id):
        return

    return await gbansdb.delete_one({"user_id": user_id})


# --------------------------------------------------
# SUDOERS
# --------------------------------------------------

async def get_sudoers() -> list:
    sudoers = await sudoersdb.find_one({"sudo": "sudo"})

    if not sudoers:
        return []

    return sudoers.get("sudoers", [])


async def add_sudo(user_id: int) -> bool:
    sudoers = await get_sudoers()

    if user_id in sudoers:
        return False

    sudoers.append(user_id)

    await sudoersdb.update_one(
        {"sudo": "sudo"},
        {"$set": {"sudoers": sudoers}},
        upsert=True,
    )

    return True


async def remove_sudo(user_id: int) -> bool:
    sudoers = await get_sudoers()

    if user_id not in sudoers:
        return False

    sudoers.remove(user_id)

    await sudoersdb.update_one(
        {"sudo": "sudo"},
        {"$set": {"sudoers": sudoers}},
        upsert=True,
    )

    return True


# --------------------------------------------------
# BLOCKED USERS
# --------------------------------------------------

async def get_banned_users() -> list:
    results = []

    async for user in blockeddb.find({"user_id": {"$gt": 0}}):
        results.append(user["user_id"])

    return results


async def get_banned_count() -> int:
    users = blockeddb.find({"user_id": {"$gt": 0}})
    users = await users.to_list(length=100000)

    return len(users)


async def is_banned_user(user_id: int) -> bool:
    user = await blockeddb.find_one({"user_id": user_id})
    return bool(user)


async def add_banned_user(user_id: int):
    if await is_banned_user(user_id):
        return

    return await blockeddb.insert_one({"user_id": user_id})


async def remove_banned_user(user_id: int):
    if not await is_banned_user(user_id):
        return

    return await blockeddb.delete_one({"user_id": user_id})
