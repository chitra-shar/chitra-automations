import datetime
import logging
import os
import sys
import pytz

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "calendar"))
import gcal_client
from shared.config import TELEGRAM_GROUP_CHAT_ID
from shared.telegram_client import send_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

SGT = pytz.timezone("Asia/Singapore")
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _format_time(iso: str) -> str:
    dt = datetime.datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = SGT.localize(dt)
    else:
        dt = dt.astimezone(SGT)
    return dt.strftime("%H:%M")


def _build_message(tomorrow: datetime.date, events: list) -> str:
    day_name = DAYS[tomorrow.weekday()]
    month_name = MONTHS[tomorrow.month]
    header = f"📅 Tomorrow — {day_name} {tomorrow.day} {month_name}"

    timed = [e for e in events if not e["all_day"]]
    all_day = [e for e in events if e["all_day"]]

    timed.sort(key=lambda e: e["start"])

    lines = [header, ""]
    for e in timed:
        time_str = _format_time(e["start"])
        loc = f" ({e['location']})" if e.get("location") else ""
        lines.append(f"• {time_str}  {e['summary']}{loc}")
    for e in all_day:
        lines.append(f"• (all day)  {e['summary']}")

    return "\n".join(lines)


def main():
    now_sgt = datetime.datetime.now(SGT)
    tomorrow = (now_sgt + datetime.timedelta(days=1)).date()
    log.info(f"Fetching events for {tomorrow}")

    events = gcal_client.get_events_for_date(tomorrow)
    single_day = [e for e in events if not (not e["all_day"] and _is_multi_day(e, tomorrow))]

    if not single_day:
        log.info("No events tomorrow — not sending message")
        return

    msg = _build_message(tomorrow, single_day)
    log.info(f"Sending reminder:\n{msg}")
    send_message(TELEGRAM_GROUP_CHAT_ID, msg)
    log.info("Reminder sent")


def _is_multi_day(event: dict, date: datetime.date) -> bool:
    if event["all_day"]:
        return False
    start = datetime.datetime.fromisoformat(event["start"])
    end = datetime.datetime.fromisoformat(event["end"])
    if start.tzinfo:
        start = start.astimezone(SGT).date()
    else:
        start = start.date()
    if end.tzinfo:
        end = end.astimezone(SGT).date()
    else:
        end = end.date()
    return start != end


if __name__ == "__main__":
    main()
