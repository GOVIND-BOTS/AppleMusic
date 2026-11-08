# 🍎 Apple Music Bot

Full multi-platform Telegram music bot by **GOVIND-BOTS**.

Based on the complete tinaxmusic / AnonXMusic architecture — all plugins, platforms, sudo tools, admins controls, and utils included.

## Platforms
- YouTube
- Spotify
- Apple Music
- SoundCloud
- Resso
- Telegram files
- Carbon

## Deploy (VPS)

```bash
sudo apt-get update && sudo apt-get install -y python3-pip ffmpeg
git clone https://github.com/GOVIND-BOTS/AppleMusic && cd AppleMusic
pip3 install -U -r requirements.txt
cp sample.env .env
# fill API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, MONGO_DB_URI, OWNER_ID
bash start
```

## Docker

```bash
docker build -t applemusic .
docker run -d --env-file .env applemusic
```

## Required vars
- `API_ID` / `API_HASH` — my.telegram.org
- `BOT_TOKEN` — @BotFather
- `STRING_SESSION` — Pyrogram v2 session (assistant)
- `MONGO_DB_URI` — MongoDB
- `OWNER_ID` — your user id

Optional: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `LOGGER_ID`

## Credits
- GOVIND-BOTS
- tinaxmusic / AnonXMusic architecture
- Pyrogram + PyTgCalls
