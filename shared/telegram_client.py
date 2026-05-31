import time
import requests
from shared.config import TELEGRAM_BOT_TOKEN


def send_message(chat_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return
        except requests.RequestException as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
