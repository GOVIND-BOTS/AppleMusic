# 🍏 AppleMusic — Telegram Music Bot 🎶

<div align="center">

![AppleMusic Banner](https://i.ibb.co/QKxTPgM/applemusic-banner.png)

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=50&duration=4000&pause=1000&color=F71C1C&center=true&vCenter=true&width=1000&height=80&lines=🍏+AppleMusic+Telegram+Bot+🎶" alt="AppleMusic animation" />

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=28&duration=3500&pause=900&color=111827&center=true&vCenter=true&width=800&height=40&lines=By+Govind+%2B+ChatGPT" alt="By Govind + ChatGPT" />

---

[![Stars](https://img.shields.io/github/stars/GOVIND-BOTS/AppleMusic?style=for-the-badge&logo=github&color=yellow)](https://github.com/GOVIND-BOTS/AppleMusic/stargazers)
[![Forks](https://img.shields.io/github/forks/GOVIND-BOTS/AppleMusic?style=for-the-badge&logo=github&color=blue)](https://github.com/GOVIND-BOTS/AppleMusic/forks)
[![Issues](https://img.shields.io/github/issues/GOVIND-BOTS/AppleMusic?style=for-the-badge&logo=github&color=red)](https://github.com/GOVIND-BOTS/AppleMusic/issues)
[![Visitors](https://api.visitorbadge.io/api/visitors?path=GOVIND-BOTS%2FAppleMusic&label=VISITORS&countColor=%23263759&style=for-the-badge)](https://github.com/GOVIND-BOTS/AppleMusic)

</div>

---

> **AppleMusic** is a polished Telegram music bot that streams and plays music from YouTube, Spotify, and Apple Music directly in Telegram voice chats.  
> Built with ❤️ by **Govind × ChatGPT** under **GOVIND-BOTS**.

---

## ✨ Features

- 🎧 Play high-quality audio/video from YouTube  
- 🍎 Fetch Apple Music metadata and previews  
- 🎵 Spotify track support (via Spotify API keys)  
- 🔊 Real-time voice chat streaming  
- ⏭️ Queue, skip, pause, and resume system  
- 🧠 Smart commands with clean UI  
- ☁️ Deploy easily on **Heroku / Koyeb / Render**

---

## 🚀 Quick Deploy

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/GOVIND-BOTS/AppleMusic)
[![Deploy to Koyeb](https://img.shields.io/badge/Deploy-Koyeb-blue?style=for-the-badge&logo=koyeb)](https://app.koyeb.com/deploy?repo=https://github.com/GOVIND-BOTS/AppleMusic)
[![Deploy to Render](https://img.shields.io/badge/Deploy-Render-0078D4?style=for-the-badge&logo=render)](https://dashboard.render.com/deploy?repo=https://github.com/GOVIND-BOTS/AppleMusic)

---

## 🧩 Project Structure

| File | Description |
|------|--------------|
| `main.py` | Bot entry point |
| `player.py` | Audio queue & control |
| `voice_chat.py` | Handles Telegram VC stream |
| `config.py` | Tokens & API credentials |
| `requirements.txt` | Dependencies |
| `Procfile` / `Dockerfile` / `app.json` | Deployment configs |

---

## ⚙️ Environment Variables

```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
APPLE_MUSIC_KEY=optional_apple_music_key
OWNER_ID=your_telegram_user_id
```

---

## 📱 How to Use

1. 🧩 **Clone the Repo**
   ```bash
   git clone https://github.com/GOVIND-BOTS/AppleMusic.git
   cd AppleMusic
   ```

2. ⚙️ **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. 🔐 **Set Environment Variables**
   ```bash
   export BOT_TOKEN=your_token_here
   ```

4. ▶️ **Run the Bot**
   ```bash
   python main.py
   ```

---

## 🧭 Commands

```
/play <song_name>  — Play or queue a song
/skip              — Skip current song
/stop              — Stop playback
/queue             — View current playlist
/nowplaying        — Show current track
/help              — Command list
```

---

## 🖼️ Screenshots

_Add screenshots of your bot UI or voice chat experience here._

---

## 🧠 Credits

> 💡 Developed by **Govind × ChatGPT**  
> 💥 Under the **GOVIND-BOTS** organization  
> ⚙️ Powered by **Pyrogram** & **Python 3.10+**

---

## 📝 License

MIT License © 2025 — GOVIND-BOTS  
You are free to use, modify, and distribute with credit.

---

<div align="center">
  
### 🎧 Made with ❤️ by <b>Govind</b> × <b>ChatGPT</b>  
⭐ Star the repo if you like it! ⭐

</div>
