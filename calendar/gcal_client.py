import datetime
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.config import GOOGLE_SERVICE_ACCOUNT_PATH, CALENDAR_ID  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SGT = pytz.timezone("Asia/Singapore")


def _service():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_PATH, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


def get_events_for_date(date: datetime.date) -> list:
    svc = _service()
    day_start = SGT.localize(datetime.datetime.combine(date, datetime.time.min))
    day_end = SGT.localize(datetime.datetime.combine(date, datetime.time.max))

    result = svc.events().list(
        calendarId=CALENDAR_ID,
        timeMin=day_start.isoformat(),
        timeMax=day_end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for item in result.get("items", []):
        start_raw = item["start"].get("dateTime") or item["start"].get("date")
        end_raw = item["end"].get("dateTime") or item["end"].get("date")
        all_day = "date" in item["start"]
        events.append({
            "summary": item.get("summary", "(no title)"),
            "start": start_raw,
            "end": end_raw,
            "location": item.get("location"),
            "all_day": all_day,
        })
    return events


def create_event(
    summary: str,
    date: datetime.date,
    start_time: datetime.time,
    end_time: datetime.time = None,
    location: str = None,
) -> str:
    svc = _service()
    if end_time is None:
        start_dt = datetime.datetime.combine(date, start_time)
        end_dt = start_dt + datetime.timedelta(hours=1)
        end_time = end_dt.time()

    start_str = SGT.localize(datetime.datetime.combine(date, start_time)).isoformat()
    end_str = SGT.localize(datetime.datetime.combine(date, end_time)).isoformat()

    body = {
        "summary": summary,
        "start": {"dateTime": start_str, "timeZone": "Asia/Singapore"},
        "end": {"dateTime": end_str, "timeZone": "Asia/Singapore"},
    }
    if location:
        body["location"] = location

    created = svc.events().insert(calendarId=CALENDAR_ID, body=body).execute()
    return created.get("htmlLink", "")
