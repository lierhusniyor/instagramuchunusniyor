"""Google Trends (ochiq RSS) orqali O'zbekistondagi kunlik trend qidiruvlarni oladi."""
import xml.etree.ElementTree as ET

import requests


def collect(geo="UZ"):
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "uz-insta-agent/0.1"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        traffic = ""
        for child in item:
            if child.tag.endswith("approx_traffic"):
                traffic = (child.text or "").strip()
        if title:
            items.append({"title": title, "traffic": traffic})
    return items
