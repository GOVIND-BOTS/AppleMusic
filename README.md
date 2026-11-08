# 🍎 Apple Music Bot

**Superfast multi-platform Telegram music bot** by [GOVIND-BOTS](https://github.com/GOVIND-BOTS)

Architecture inspired by tinaxmusic / AnonXMusic style bots — clean package layout, multi-assistant ready, multi-platform play.

## Platforms

| Platform | Support |
|---|---|
| YouTube | Search + links + playlists via yt-dlp |
| Spotify | Track links → YouTube resolve |
| Apple Music | Links → title resolve → YouTube |
| SoundCloud | Direct via yt-dlp |
| Resso | Links → YouTube resolve |
| Telegram | Audio / voice / video files |

## Commands

| Command | Description |
|---|---|
| `/play <name\|url>` | Play audio in VC |
| `/vplay <name\|url>` | Play video in VC |
| `/pause` | Pause |
| `/resume` | Resume |
| `/skip` | Next track |
| `/stop` | Stop + clear queue |
| `/queue` | Show queue |
| `/ping` | Latency |

## Deploy

### Variables (`sample.env`)

```
API_ID=
API_HASH=
BOT_TOKEN=
STRING_SESSION=
MONGO_DB_URI=
OWNER_ID=
LOGGER_ID=
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
BOT_NAME=Apple Music
```

### VPS

```bash
git clone https://github.com/GOVIND-BOTS/AppleMusic
cd AppleMusic
pip3 install -U -r requirements.txt
cp sample.env .env
# fill .env
bash start
```

### Docker

```bash
docker build -t applemusic .
docker run -d --env-file .env applemusic
```

### Heroku

Use `app.json` + `heroku.yml` (container stack).

## Notes

1. Assistant account (`STRING_SESSION`) must be in the group.
2. Start an **active voice chat** before `/play`.
3. Bot needs admin rights for best control UX.
4. Spotify optional — without keys, Spotify links won't resolve.

## Credits

- GOVIND-BOTS
- Pyrogram + PyTgCalls + yt-dlp
