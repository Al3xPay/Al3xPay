import json
import os
import time
from datetime import datetime, timezone, timedelta

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION = os.environ["TG_SESSION"]
TARGET = "Al3xPay"          # чей статус проверяем
OUT_FILE = "output/portfolio/tg-status.json"   # рядом с index.html

MSK = timezone(timedelta(hours=3))   # Москва = UTC+3 всегда


def describe(status):
    """UserStatus* -> данные для сайта"""
    if isinstance(status, (UserStatusOnline, UserStatusRecently)):
        return {"online": True}
    if isinstance(status, UserStatusOffline):
        was = getattr(status, "last_online", None)
        if was:
            mins = int((datetime.now(timezone.utc) - was).total_seconds() // 60)
            msk = was.astimezone(MSK)
            # меньше суток — только время, больше — дата и время
            label = msk.strftime("%d.%m %H:%M") if mins >= 1440 else msk.strftime("%H:%M")
            return {"online": mins <= 5, "last_label": label, "ago_min": mins}
    return {"online": False}


def main():
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    client.connect()
    if not client.is_user_authorized():
        raise SystemExit("Сессия невалидна — перегенерируй TG_SESSION через gen_session.py")

    entity = client.get_entity(TARGET)
    full = client(GetFullUserRequest(entity))
    data = describe(full.full_user.status)
    if "last_label" not in data:
        data["last_label"] = ""
    data["checked_at"] = int(time.time())

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print("OK:", data)
    client.disconnect()


if __name__ == "__main__":
    main()
