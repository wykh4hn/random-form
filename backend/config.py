
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")


def _int(name, default):
    raw = os.getenv(name)
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


# google sheets
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE") or str(BASE_DIR / "credentials.json")
SHEET_ID = os.getenv("SHEET_ID", "")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "Leads")

# email
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "resend").strip().lower()
EMAIL_API_KEY = os.getenv("EMAIL_API_KEY", "")
# resend lends you onboarding@resend.dev before you verify a domain of your own
EMAIL_FROM = os.getenv("EMAIL_FROM", "MyForm <onboarding@resend.dev>")
EMAIL_REPLY_TO = os.getenv("EMAIL_REPLY_TO", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

# reminder rules 
REMINDER_AFTER_HOURS = _int("REMINDER_AFTER_HOURS", 24)   # how long a lead may sit unanswered
REMINDER_GAP_HOURS = _int("REMINDER_GAP_HOURS", 24)       # min spacing between two reminders
REMINDER_MAX = _int("REMINDER_MAX", 3)                    # stop nagging after this many

# web
PORT = _int("PORT", 5000)
DEBUG = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
# only needed if the form is hosted somewhere other than this flask app
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "")
DUPLICATE_WINDOW_HOURS = _int("DUPLICATE_WINDOW_HOURS", 12)
RATE_LIMIT_MAX = _int("RATE_LIMIT_MAX", 5)
RATE_LIMIT_WINDOW_MIN = _int("RATE_LIMIT_WINDOW_MIN", 10)

TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S"
