import re

import aiohttp


class AppleAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/music\.apple\.com\/)(.*)$"

    async def valid(self, url: str):
        return bool(re.search(self.regex, url or ""))

    async def track(self, url: str):
        """
        Apple Music pages expose title via og tags.
        Playback is resolved through YouTube search.
        """
        title = "Apple Music Track"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    html = await resp.text()
            m = re.search(
                r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
                html,
                re.I,
            )
            if not m:
                m = re.search(
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
                    html,
                    re.I,
                )
            if m:
                title = m.group(1).strip()
        except Exception:
            pass
        return {
            "title": title,
            "query": title,
            "link": url,
            "duration": "0:00",
            "thumbnail": None,
        }

    async def resolve(self, url: str):
        data = await self.track(url)
        return data["query"] if data else None
