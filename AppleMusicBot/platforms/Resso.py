import re

import aiohttp


class RessoAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/(?:www\.|m\.)?resso\.com\/)(.*)$"

    async def valid(self, url: str):
        return bool(re.search(self.regex, url or ""))

    async def track(self, url: str):
        title = "Resso Track"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    html = await resp.text()
            m = re.search(
                r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
                html,
                re.I,
            )
            if m:
                title = m.group(1).strip()
        except Exception:
            pass
        return {"title": title, "query": title, "link": url}

    async def resolve(self, url: str):
        data = await self.track(url)
        return data["query"] if data else None
