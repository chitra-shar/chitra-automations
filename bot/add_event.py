import datetime
import json
import logging
import os
import sys

import anthropic

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "calendar"))
import gcal_client
from shared.config import CLAUDE_API_KEY, TELEGRAM_GROUP_CHAT_ID
from shared.telegram_client import send_message

log = logging.getLogger(__name__)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

SYSTEM_PROMPT = """You are a calendar assistant. Extract event details from a natural language message.
Return JSON only. No explanation, no markdown, no backticks.

Timezone: Asia/Singapore

If the message is a calendar event, return:
{
  "intent": "add_event",
  "summary": "event title",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM or null",
  "location": "location or null"
}

If end_time is null, caller defaults to start_time + 1 hour.
If not a calendar event, return: {"intent": "unknown"}"""


def _parse_with_claude(text: str, today: datetime.date) -> dict:
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    user_prompt = f"Today's date: {today.isoformat()}\n\n{text}"
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`").strip()
    return json.loads(raw)


def _format_receipt(summary: str, date: datetime.date, start_time: datetime.time, end_time: datetime.time) -> str:
    day_name = DAYS[date.weekday()]
    month_name = MONTHS[date.month]
    start_str = start_time.strftime("%-I:%M%p").lower().replace(":00", "").rstrip("m") + "m"
    end_str = end_time.strftime("%-I:%M%p").lower().replace(":00", "").rstrip("m") + "m"
    return f"✅ {summary} added — {day_name} {date.day} {month_name}, {start_str}–{end_str}"


def handle(text: str, chat_id: int) -> None:
    today = datetime.date.today()
    try:
        parsed = _parse_with_claude(text, today)
    except Exception as e:
        log.error(f"Claude parse error: {e}")
        return

    if parsed.get("intent") != "add_event":
        return

    try:
        date = datetime.date.fromisoformat(parsed["date"])
        start_time = datetime.time.fromisoformat(parsed["start_time"])
        end_time = (
            datetime.time.fromisoformat(parsed["end_time"])
            if parsed.get("end_time")
            else None
        )
        location = parsed.get("location")

        if end_time is None:
            import datetime as dt
            end_dt = dt.datetime.combine(date, start_time) + dt.timedelta(hours=1)
            end_time = end_dt.time()

        gcal_client.create_event(
            summary=parsed["summary"],
            date=date,
            start_time=start_time,
            end_time=end_time,
            location=location,
        )

        receipt = _format_receipt(parsed["summary"], date, start_time, end_time)
        send_message(chat_id, receipt)
        log.info(f"Event created: {receipt}")
    except Exception as e:
        log.error(f"Event creation error: {e}")
