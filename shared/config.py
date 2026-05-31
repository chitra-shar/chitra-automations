from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_GROUP_CHAT_ID = int(os.environ["TELEGRAM_GROUP_CHAT_ID"])
GOOGLE_SERVICE_ACCOUNT_PATH = os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"]
CALENDAR_ID = os.environ["CALENDAR_ID"]
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
