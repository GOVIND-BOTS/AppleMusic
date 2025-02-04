from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN
from player import download_youtube_audio, get_spotify_track
from voice_chat import start_stream

bot = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

queue = []  # Music queue for skip command

@bot.on_message(filters.command("play"))
async def play_music(client, message):
    query = message.text.split(" ", 1)[1]
    message.reply_text(f"Searching for: {query}...")
    
    filename = download_youtube_audio(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
    queue.append(filename)
    
    if len(queue) == 1:
        await start_stream(message.chat.id, filename)
        await message.reply_text(f"Playing: {query}")

@bot.on_message(filters.command("skip"))
async def skip_music(client, message):
    if len(queue) > 1:
        queue.pop(0)
        await start_stream(message.chat.id, queue[0])
        await message.reply_text("⏭ Skipped to next song!")
    else:
        await message.reply_text("❌ Queue is empty!")

@bot.on_message(filters.command("stop"))
async def stop_music(client, message):
    queue.clear()
    await message.reply_text("🛑 Music stopped!")

bot.run()
