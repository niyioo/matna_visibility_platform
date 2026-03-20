from datetime import date, timedelta
from django.db.models import Avg, Sum
from apps.production.models import ProductionEntry
from apps.inventory.models import InventoryBalance


def get_dashboard_snapshot():
    latest_entry = ProductionEntry.objects.order_by("-production_date", "-created_at").first()

    balances = InventoryBalance.objects.select_related("item").all()
    balance_map = {balance.item.code: balance.quantity_on_hand for balance in balances}

    if latest_entry:
        snapshot_date = latest_entry.production_date
        day_queryset = ProductionEntry.objects.filter(production_date=snapshot_date)

        aggregates = day_queryset.aggregate(
            total_inflow=Sum("cassava_inflow_tons"),
            total_output=Sum("starch_output_tons"),
            average_yield=Avg("yield_percent"),
            total_downtime=Sum("downtime_minutes"),
        )
    else:
        snapshot_date = None
        aggregates = {
            "total_inflow": 0,
            "total_output": 0,
            "average_yield": 0,
            "total_downtime": 0,
        }

    return {
        "snapshot_date": snapshot_date,
        "latest_inflow": aggregates["total_inflow"] or 0,
        "latest_output": aggregates["total_output"] or 0,
        "latest_yield": aggregates["average_yield"] or 0,
        "latest_downtime": aggregates["total_downtime"] or 0,
        "raw_cassava_stock": balance_map.get("RAW_CASSAVA", 0),
        "finished_starch_stock": balance_map.get("FINISHED_STARCH", 0),
    }


def get_period_summary(period: str, start_date=None, end_date=None):
    today = date.today()

    if start_date and end_date:
        queryset = ProductionEntry.objects.filter(
            production_date__gte=start_date,
            production_date__lte=end_date,
        )
        actual_start_date = start_date
        actual_end_date = end_date
    else:
        if period == "daily":
            actual_start_date = today
        elif period == "weekly":
            actual_start_date = today - timedelta(days=6)
        elif period == "monthly":
            actual_start_date = today.replace(day=1)
        else:
            actual_start_date = today

        actual_end_date = today

        queryset = ProductionEntry.objects.filter(
            production_date__gte=actual_start_date,
            production_date__lte=actual_end_date,
        )

    aggregates = queryset.aggregate(
        total_inflow=Sum("cassava_inflow_tons"),
        total_output=Sum("starch_output_tons"),
        average_yield=Avg("yield_percent"),
        total_downtime=Sum("downtime_minutes"),
    )

    return {
        "period": period,
        "start_date": actual_start_date,
        "end_date": actual_end_date,
        "total_inflow": aggregates["total_inflow"] or 0,
        "total_output": aggregates["total_output"] or 0,
        "average_yield": aggregates["average_yield"] or 0,
        "total_downtime": aggregates["total_downtime"] or 0,
        "entries_count": queryset.count(),
    }