"""Hisobotni Telegram bot yoki email (Gmail SMTP) orqali yuboradi."""
import os
import smtplib
from email.message import EmailMessage

import requests


def _chunks(text, size=4000):
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def send_telegram(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    for part in _chunks(text):
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": part},
            timeout=30,
        )
        resp.raise_for_status()
    return True


def send_email(text):
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    to = os.environ.get("EMAIL_TO") or user
    if not user or not password:
        return False
    msg = EmailMessage()
    msg["Subject"] = "Kunlik Instagram hisobot"
    msg["From"] = user
    msg["To"] = to
    msg.set_content(text)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    return True


def send(text):
    sent = []
    if send_telegram(text):
        sent.append("telegram")
    if send_email(text):
        sent.append("email")
    if not sent:
        print("Telegram/email sozlanmagan, hisobot shu yerda:\n")
        print(text)
    else:
        print("Yuborildi: " + ", ".join(sent))
    return sent
