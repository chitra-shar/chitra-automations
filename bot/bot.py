import logging
import os
import sys
import time

import requests

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "bot"))
from shared.config import TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_CHAT_ID
import add_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def get_updates(offset: int) -> list:
    try:
        resp = requests.get(
            f"{BASE_URL}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35,
        )
        resp.raise_for_status()
        return resp.json().get("result", [])
    except requests.RequestException as e:
        log.warning(f"getUpdates error: {e}")
        return []


def main():
    log.info("Bot starting")
    offset = 0
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message") or update.get("edited_message")
            if not msg:
                continue
            chat_id = msg.get("chat", {}).get("id")
            if chat_id != TELEGRAM_GROUP_CHAT_ID:
                continue
            text = msg.get("text", "")
            if not text:
                continue
            log.info(f"Handling message: {text!r}")
            add_event.handle(text, chat_id)


if __name__ == "__main__":
    main()
