# -*- coding: utf-8 -*-
"""CI-версия: запускается GitHub Actions по расписанию.
Читает секреты TG_API_ID / TG_API_HASH / TG_SESSION,
проверяет статус @TARGET и пишет tg-status.json в корень репозитория."""

import json
import os
import time
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION = os.environ["TG_SESSION"]
TARGET = "Al3xPay"          # чей статус проверяем
OUT_FILE = "output/portfolio/tg-status.json"   # рядом с index.html


def status_to_bool(status):
    if isinstance(status, UserStatusOnline):
        return True
    if isinstance(status, UserStatusRecently):
        return True
    if isinstance(status, UserStatusOffline):
        was = getattr(status, "last_online", None)
        if was:
            mins_ago = (datetime.now(timezone.utc) - was).total_seconds() / 60
            return mins_ago <= 5   # «недавно был» считаем онлайн
    return False


def main():
    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    client.connect()
    if not client.is_user_authorized():
        raise SystemExit("Сессия невалидна — перегенерируй TG_SESSION через gen_session.py")

    entity = client.get_entity(TARGET)
    full = client(GetFullUserRequest(entity))
    data = {
        "online": status_to_bool(full.full_user.status),
        "checked_at": int(time.time()),
    }
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print("OK:", data)
    client.disconnect()


if __name__ == "__main__":
    main()
