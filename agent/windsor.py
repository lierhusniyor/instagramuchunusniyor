"""Windsor.ai (MCP) orqali Instagram: o'z akkaunt ma'lumoti va post qo'yish.

Instagram Graph API, IG_USER_ID va Meta token KERAK EMAS: faqat WINDSOR_API_KEY.
Instagram akkaunt windsor.ai'da ulangan bo'lishi kerak.
"""
import json
import os
import time

import requests

MCP_URL = "https://mcp.windsor.ai/"
TIMEOUT = 120

POST_FIELDS = [
    "media_id", "timestamp", "media_type", "media_caption", "media_like_count",
    "media_comments_count", "media_permalink", "media_reach", "media_saved", "media_shares",
]


class WindsorError(RuntimeError):
    pass


class WindsorMCP:
    def __init__(self, api_key):
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        })
        self._id = 0
        self._rpc("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "uz-insta-agent", "version": "1.0"},
        })
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _post(self, payload):
        resp = self.s.post(MCP_URL, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        sid = resp.headers.get("mcp-session-id")
        if sid:
            self.s.headers["mcp-session-id"] = sid
        if not resp.text.strip():
            return None
        if "text/event-stream" in resp.headers.get("content-type", ""):
            for line in resp.text.splitlines():
                if line.startswith("data:") and line[5:].strip():
                    return json.loads(line[5:].strip())
            return None
        return resp.json()

    def _rpc(self, method, params=None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        resp = self._post(msg)
        if resp and "error" in resp:
            raise WindsorError(resp["error"])
        return (resp or {}).get("result") or {}

    def call(self, tool, arguments):
        res = self._rpc("tools/call", {"name": tool, "arguments": arguments})
        text = "".join(c.get("text", "") for c in res.get("content", []))
        if res.get("isError"):
            raise WindsorError(text or "Windsor xatosi")
        try:
            return json.loads(text)
        except ValueError:
            return text

    def get_data(self, connector, fields, **kwargs):
        """Katta so'rov 'pending' qaytarsa, o'sha so'rovni takrorlab kutadi."""
        args = {"connector": connector, "fields": fields, **kwargs}
        for _ in range(40):
            res = self.call("get_data", args)
            if isinstance(res, dict) and res.get("status") == "pending":
                time.sleep(min(float(res.get("poll_after_seconds") or 10), 30))
                continue
            if isinstance(res, list):
                return res
            return res.get("data", []) if isinstance(res, dict) else []
        raise WindsorError("get_data tugamadi (vaqt tugadi)")

    def instagram_account(self):
        """Windsor'ga ulangan Instagram akkaunt (id, name). IG_USER_ID qo'lda kerak emas."""
        data = self.call("get_connectors", {"include_options": False, "include_actions": False})
        conns = data.get("result", []) if isinstance(data, dict) else data
        for conn in conns or []:
            if conn.get("id") == "instagram" and conn.get("accounts"):
                wanted = os.environ.get("WINDSOR_IG_ACCOUNT")
                for acc in conn["accounts"]:
                    if not wanted or acc["id"] == wanted:
                        return acc
        raise WindsorError("Windsor'da Instagram ulanmagan (windsor.ai > Connectors > Instagram).")

    def action(self, action, params):
        acc = self.instagram_account()
        return self.call("execute_action", {
            "connector": "instagram", "action": action, "account": acc["id"], "params": params,
        })


def collect(client, lookback_days):
    """O'z akkaunt postlari: analyze.py kutadigan shaklga keltiriladi."""
    acc = client.instagram_account()
    profile = client.get_data(
        "instagram", ["username", "followers_count"], accounts=[acc["id"]]
    )
    followers = (profile[0].get("followers_count") if profile else 0) or 0
    rows = client.get_data(
        "instagram", POST_FIELDS, accounts=[acc["id"]], date_preset=f"last_{lookback_days}d"
    )
    posts = []
    for row in rows:
        if not row.get("timestamp"):
            continue
        posts.append({
            "caption": row.get("media_caption") or "",
            "like_count": row.get("media_like_count") or 0,
            "comments_count": row.get("media_comments_count") or 0,
            "media_type": row.get("media_type"),
            "permalink": row.get("media_permalink") or "",
            "timestamp": str(row["timestamp"]),
            "reach": row.get("media_reach") or 0,
            "saved": row.get("media_saved") or 0,
            "shares": row.get("media_shares") or 0,
        })
    return [{"username": acc.get("name") or "akkaunt", "followers": followers, "posts": posts}]


def publish(client, item):
    """Navbatdagi elementni Instagram'ga joylaydi. item: agent/poster.py dagi navbat elementi."""
    kind = item["type"]
    caption = item.get("caption") or None
    if kind == "image":
        return client.action("create_image_post", {"image_url": item["url"], "caption": caption})
    if kind == "carousel":
        return client.action("create_carousel_post", {"image_urls": item["urls"], "caption": caption})
    if kind == "reel":
        return client.action("create_video_post", {"video_url": item["url"], "caption": caption})
    if kind == "story":
        key = "video_url" if item["url"].lower().split("?")[0].endswith((".mp4", ".mov")) else "image_url"
        return client.action("create_story", {key: item["url"]})
    raise WindsorError(f"Noma'lum post turi: {kind}")
