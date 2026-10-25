"""Read-only queries behind the analytics endpoints. Voided entries are always excluded."""
from django.db.models import Avg, Count, Sum

from apps.production.models import ProductionEntry


def active_entries(start_date, end_date):
    return ProductionEntry.objects.active().filter(production_date__range=(start_date, end_date))


def aggregate_entries(start_date, end_date) -> dict:
    return active_entries(start_date, end_date).aggregate(
        total_inflow=Sum("cassava_inflow_tons"),
        total_output=Sum("starch_output_tons"),
        total_downtime=Sum("downtime_minutes"),
        average_downtime=Avg("downtime_minutes"),
        entries_count=Count("id"),
    )


def daily_series(start_date, end_date) -> list[dict]:
    return list(
        active_entries(start_date, end_date)
        .order_by("production_date")
        .values(
            "production_date",
            "cassava_inflow_tons",
            "starch_output_tons",
            "yield_percent",
            "downtime_minutes",
        )
    )


def latest_entry():
    return ProductionEntry.objects.active().order_by("-production_date", "-created_at").first()
