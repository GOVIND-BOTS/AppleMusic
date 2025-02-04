import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

def download_youtube_audio(url):
    options = {
        'format': 'bestaudio/best',
        'outtmpl': 'music.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
        return "music.mp3"

def get_spotify_track(track_url):
    track_info = sp.track(track_url)
    return track_info['name'], track_info['artists'][0]['name']
