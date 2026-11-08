import re


class SoundAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/(?:m\.|www\.)?soundcloud\.com\/)(.*)$"

    async def valid(self, url: str):
        return bool(re.search(self.regex, url or ""))

    async def resolve(self, url: str):
        # yt-dlp can stream soundcloud directly
        return url
