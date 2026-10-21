#!/usr/bin/env python3
"""5 ta reel videoni bir buyruq bilan yasaydi: python3 build_all.py"""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "videos"
OUT.mkdir(exist_ok=True)

REELS = {
    "reel1_nega_korilmaydi": {
        "bg": ["#0f172a", "#be123c"],
        "slides": [
            ("Reelingiz nega ko'rilmaydi?", 2.5),
            ("1. Boshi zerikarli", 2.5),
            ("Birinchi 2 soniyada qiziqtiring", 3),
            ("2. Video juda uzun", 2.5),
            ("7-15 soniya eng yaxshi", 3),
            ("3. Har xil mavzu", 2.5),
            ("Bitta yo'nalishda qoling", 3),
            ("Saqlab qo'ying!", 2),
        ],
    },
    "reel2_algoritm": {
        "bg": ["#0f172a", "#7c3aed"],
        "slides": [
            ("Instagram algoritmi nimani yaxshi ko'radi?", 3),
            ("Oxirigacha ko'rilgan video", 3),
            ("Qayta-qayta ko'rilgan video", 3),
            ("Saqlangan va ulashilgan video", 3),
            ("Izohlar va javoblar", 3),
            ("Sizning videongiz shularga mosmi?", 3),
        ],
    },
    "reel3_bio": {
        "bg": ["#0f172a", "#0369a1"],
        "slides": [
            ("Bio ni 3 qatorda to'g'ri yozing", 3),
            ("1. Siz kimsiz?", 2.5),
            ("2. Odamlar nima oladi?", 3),
            ("3. Keyingi qadam: obuna bo'ling", 3),
            ("Ismingizga ham kalit so'z qo'shing", 3),
            ("Hozir bio ni tekshiring!", 2.5),
        ],
    },
    "reel4_vaqt": {
        "bg": ["#0f172a", "#047857"],
        "slides": [
            ("Qaysi vaqtda video qo'yish kerak?", 3),
            ("Hamma uchun bitta vaqt yo'q", 3),
            ("Insights bo'limini oching", 3),
            ("Auditoriya faol vaqtini toping", 3),
            ("Shu vaqtda joylang", 3),
            ("Natijani 2 haftada solishtiring", 3),
        ],
    },
    "reel5_obunachi": {
        "bg": ["#0f172a", "#c2410c"],
        "slides": [
            ("Obunachi ko'paytirishning 3 qadami", 3),
            ("1. Foydali kontent", 2.5),
            ("2. Muntazam joylash", 2.5),
            ("3. Izohlarga javob berish", 3),
            ("Sabr qiling: natija 2-3 oyda", 3),
            ("Obuna bo'ling!", 2.5),
        ],
    },
}

for name, data in REELS.items():
    cfg = {
        "slides": [{"text": t, "seconds": s} for t, s in data["slides"]],
        "bg1": data["bg"][0],
        "bg2": data["bg"][1],
    }
    cfg_path = OUT / f"{name}.json"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    subprocess.run(
        ["python3", str(HERE / "make_reel.py"), str(cfg_path), str(OUT / f"{name}.mp4")],
        check=True,
    )
