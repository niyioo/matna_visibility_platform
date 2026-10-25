from datetime import date, datetime, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

PERIODS = ("daily", "weekly", "monthly")

# Served to the SPA (GET /api/analytics/config/) so labels never drift from logic.
PERIOD_DEFINITIONS = [
    {"value": "daily", "label": "Today", "description": "Today's production"},
    {"value": "weekly", "label": "Last 7 days", "description": "Today and the 6 days before"},
    {"value": "monthly", "label": "Month to date", "description": "From the 1st of this month"},
]


def max_range_days() -> int:
    return settings.PLATFORM_SETTINGS["MAX_RANGE_DAYS"]


def trend_window_days() -> int:
    return settings.PLATFORM_SETTINGS["TREND_WINDOW_DAYS"]


def parse_iso_date(value, field: str):
    if value in (None, ""):
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValidationError({field: f"Invalid date '{value}'. Use YYYY-MM-DD."}) from exc


def validate_period(period) -> str:
    period = (period or "daily").lower()
    if period not in PERIODS:
        raise ValidationError({"period": f"Period must be one of: {', '.join(PERIODS)}."})
    return period


def _check_range(start: date, end: date) -> tuple[date, date]:
    if start > end:
        raise ValidationError({"start_date": "Start date must be on or before end date."})
    limit = max_range_days()
    if (end - start).days + 1 > limit:
        raise ValidationError({"end_date": f"Date range cannot exceed {limit} days."})
    return start, end


def period_range(period: str, today: date | None = None) -> tuple[date, date]:
    today = today or timezone.localdate()
    if period == "weekly":
        return today - timedelta(days=6), today
    if period == "monthly":
        return today.replace(day=1), today
    return today, today


def resolve_range(params, *, default_period: str | None = None, default_days: int | None = None):
    """
    Resolve (start, end) from query params in the plant's timezone.

    Explicit start_date / end_date win. Otherwise a `period` (daily/weekly/monthly)
    is used, and failing that the last `default_days` days. Always bounded.
    """
    default_days = default_days or trend_window_days()
    start = parse_iso_date(params.get("start_date"), "start_date")
    end = parse_iso_date(params.get("end_date"), "end_date")
    today = timezone.localdate()

    if start or end:
        end = end or today
        start = start or end - timedelta(days=default_days - 1)
        return _check_range(start, end)

    period = params.get("period") or default_period
    if period:
        return period_range(validate_period(period), today)

    return today - timedelta(days=default_days - 1), today


def previous_range(start: date, end: date) -> tuple[date, date]:
    """The window of equal length immediately before [start, end]."""
    length = (end - start).days + 1
    return start - timedelta(days=length), start - timedelta(days=1)
