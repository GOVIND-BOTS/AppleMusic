from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from config import API_ID, API_HASH, BOT_TOKEN
from pyrogram import Client

app = Client("MusicVC", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
vc = PyTgCalls(app)

async def start_stream(chat_id, filename):
    await vc.join_group_call(chat_id, AudioPiped(filename))
