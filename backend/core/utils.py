from datetime import date, datetime, timedelta, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def today_range() -> tuple[datetime, datetime]:
    now = utcnow()
    start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start, end


def week_end(from_date: date) -> date:
    return from_date + timedelta(days=7)
