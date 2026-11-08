import re
from typing import Union

import config

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
except Exception:
    spotipy = None


class SpotifyAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/open.spotify.com\/)(.*)$"
        self.client = None
        if (
            spotipy
            and config.SPOTIFY_CLIENT_ID
            and config.SPOTIFY_CLIENT_SECRET
        ):
            try:
                self.client = spotipy.Spotify(
                    auth_manager=SpotifyClientCredentials(
                        client_id=config.SPOTIFY_CLIENT_ID,
                        client_secret=config.SPOTIFY_CLIENT_SECRET,
                    )
                )
            except Exception:
                self.client = None

    async def valid(self, link: str):
        return bool(re.search(self.regex, link or ""))

    async def track(self, link: str):
        if not self.client:
            return None
        track = self.client.track(link)
        name = track.get("name", "Unknown")
        artists = ", ".join(a["name"] for a in track.get("artists", []))
        query = f"{name} {artists}"
        thumb = (track.get("album", {}).get("images") or [{}])[0].get("url")
        duration = int(track.get("duration_ms", 0) / 1000)
        mins, secs = divmod(duration, 60)
        return {
            "title": f"{name} - {artists}",
            "query": query,
            "duration": f"{mins}:{secs:02d}",
            "thumbnail": thumb,
            "link": link,
        }

    async def resolve(self, link: str) -> Union[str, None]:
        data = await self.track(link)
        return data["query"] if data else None
