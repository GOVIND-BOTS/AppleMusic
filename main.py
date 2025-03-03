import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN
from player import download_youtube_audio, get_apple_music_track
from voice_chat import start_stream, join_voice_chat

bot = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
queue = []  # Music queue for skip command

async def search_youtube(query):
    from yt_dlp import YoutubeDL
    ydl_opts = {"format": "bestaudio"}
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            return info['entries'][0]['url'] if info['entries'] else None
        except:
            return None

@bot.on_message(filters.command("play"))
async def play_music(client, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply_text("⚠️ **Please provide a song name!**")

    await message.reply_text(f"🔍 **Searching for:** `{query}` ...")
    
    if "music.apple.com" in query:
        filename = get_apple_music_track(query)
    else:
        youtube_url = await search_youtube(query)
        if not youtube_url:
            return await message.reply_text("❌ **Song not found!**")
        filename = download_youtube_audio(youtube_url)

    queue.append(filename)

    if len(queue) == 1:
        chat_id = message.chat.id
        await join_voice_chat(chat_id)
        await start_stream(chat_id, filename)
        await message.reply_text(f"▶ **Now Playing:** `{query}`")

@bot.on_message(filters.command("skip"))
async def skip_music(client, message: Message):
    if len(queue) > 1:
        queue.pop(0)
        await start_stream(message.chat.id, queue[0])
        await message.reply_text("⏭ **Skipped to next song!**")
    else:
        await message.reply_text("❌ **Queue is empty!**")

@bot.on_message(filters.command("stop"))
async def stop_music(client, message: Message):
    queue.clear()
    await message.reply_text("🛑 **Music stopped!**")

bot.run()
