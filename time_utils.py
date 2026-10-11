from datetime import datetime, timezone
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


def to_ist(value: str | datetime) -> datetime:
    """Convert a stored UTC event timestamp to an aware IST datetime.

    SQLite CURRENT_TIMESTAMP historically stores a naive UTC string. Aware
    values retain their declared instant, so localized values are not shifted
    twice.
    """
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(IST)


def format_ist(value: str | datetime | None) -> str:
    if not value:
        return ""
    return to_ist(value).strftime("%d %b %Y, %H:%M:%S IST")
