import os
import requests
from urllib.parse import urljoin

class CanvasClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/") + "/"
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _url(self, path: str) -> str:
        if path.startswith("/"):
            path = path[1:]
        return urljoin(self.base_url, path)

    def get_paginated(self, path: str, params: dict | None = None) -> list[dict]:
        url = self._url(path)
        out: list[dict] = []
        params = params or {}

        while url:
            r = self.session.get(url, params=params, timeout=30)
            r.raise_for_status()
            out.extend(r.json())

            # Canvas pagination uses link headers
            next_url = None
            link = r.headers.get("Link", "")
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.splot(";")[0].strip()[1:-1]
                    break
            url = next_url
            params = None # Next url already includes params

        return out