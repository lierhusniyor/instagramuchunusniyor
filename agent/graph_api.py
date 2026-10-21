"""Instagram Graph API (Business Discovery) orqali ochiq akkaunt postlarini oladi.

Talab: o'zingizning Instagram Business/Creator akkauntingiz (IG_USER_ID) va
Meta developer ilovadan olingan token (IG_ACCESS_TOKEN). Business Discovery faqat
ochiq Business/Creator akkauntlarni o'qiy oladi; boshqalari o'tkazib yuboriladi.
"""
import os

import requests

BASE = "https://graph.facebook.com"


def fetch_account(username, ig_user_id, token, version, limit):
    fields = (
        "business_discovery.username({u}){{username,followers_count,media_count,"
        "media.limit({n}){{caption,like_count,comments_count,media_type,permalink,timestamp}}}}"
    ).format(u=username, n=limit)
    resp = requests.get(
        f"{BASE}/{version}/{ig_user_id}",
        params={"fields": fields, "access_token": token},
        timeout=30,
    )
    data = resp.json()
    if resp.status_code != 200 or "business_discovery" not in data:
        message = data.get("error", {}).get("message", f"HTTP {resp.status_code}")
        raise RuntimeError(message)
    bd = data["business_discovery"]
    return {
        "username": bd.get("username", username),
        "followers": bd.get("followers_count") or 0,
        "posts": bd.get("media", {}).get("data", []),
    }


def collect(config):
    token = os.environ.get("IG_ACCESS_TOKEN")
    ig_user_id = os.environ.get("IG_USER_ID")
    if not token or not ig_user_id:
        return [], ["IG_ACCESS_TOKEN / IG_USER_ID yo'q: Instagram postlari olinmadi (faqat trendlar)."]
    accounts, warnings = [], []
    for acc in config["accounts"]:
        try:
            accounts.append(
                fetch_account(
                    acc["username"],
                    ig_user_id,
                    token,
                    config.get("graph_version", "v21.0"),
                    config.get("posts_per_account", 25),
                )
            )
        except Exception as exc:  # noqa: BLE001 - har bir akkaunt alohida
            warnings.append(f"@{acc['username']} o'tkazib yuborildi: {exc}")
    return accounts, warnings
