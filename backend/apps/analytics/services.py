"""
KPI calculations, period comparisons, anomaly detection and operational alerts.

Yield is always computed as total starch output / total cassava inflow over the
window (tonnage-weighted). Averaging daily yield percentages would give a small
day the same weight as a full one and misstate plant efficiency.
"""
import statistics
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.inventory.models import InventoryBalance
from common.constants import FINISHED_STARCH_CODE, RAW_CASSAVA_CODE
from common.dates import PERIOD_DEFINITIONS, previous_range

from .selectors import aggregate_entries, daily_series, latest_entry

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}

# For each KPI: is a higher value good for the operation?
HIGHER_IS_BETTER = {
    "total_inflow": True,
    "total_output": True,
    "yield_percent": True,
    "total_downtime": False,
    "average_downtime": False,
    "entries_count": True,
}


def _thresholds():
    return settings.OPERATIONS_THRESHOLDS


def _num(value, places=2):
    if value is None:
        return None
    return round(float(value), places)


def _weighted_yield(total_inflow, total_output):
    if not total_inflow:
        return None
    return float(Decimal(total_output or 0) / Decimal(total_inflow) * 100)


def summarize(start_date, end_date) -> dict:
    agg = aggregate_entries(start_date, end_date)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "days": (end_date - start_date).days + 1,
        "entries_count": agg["entries_count"],
        "total_inflow": _num(agg["total_inflow"] or 0),
        "total_output": _num(agg["total_output"] or 0),
        "yield_percent": _num(_weighted_yield(agg["total_inflow"], agg["total_output"])),
        "total_downtime": agg["total_downtime"] or 0,
        "average_downtime": _num(agg["average_downtime"]),
    }


def compare(current: dict, previous: dict) -> dict:
    comparison = {}
    for key, higher_is_better in HIGHER_IS_BETTER.items():
        cur, prev = current.get(key), previous.get(key)
        if cur is None or prev is None:
            comparison[key] = {"current": cur, "previous": prev, "change": None, "change_percent": None, "trend": "flat", "favourable": None}
            continue
        change = cur - prev
        change_percent = (change / prev * 100) if prev else None
        trend = "up" if change > 0 else "down" if change < 0 else "flat"
        favourable = None if trend == "flat" else (change > 0) == higher_is_better
        comparison[key] = {
            "current": cur,
            "previous": prev,
            "change": _num(change),
            "change_percent": _num(change_percent, 1),
            "trend": trend,
            "favourable": favourable,
        }
    return comparison


def get_period_summary(start_date, end_date, period=None) -> dict:
    current = summarize(start_date, end_date)
    prev_start, prev_end = previous_range(start_date, end_date)
    previous = summarize(prev_start, prev_end)

    return {
        "period": period,
        **current,
        # Backwards-compatible alias; this is now the tonnage-weighted yield.
        "average_yield": current["yield_percent"],
        "previous": previous,
        "comparison": compare(current, previous),
    }


# Smallest spread treated as meaningful. Without a floor, a run of identical
# days (std = 0) would either hide every outlier or flag rounding noise.
YIELD_STD_FLOOR = 0.5       # percentage points
DOWNTIME_STD_FLOOR = 10.0   # minutes


def _stats(values, floor=0.0):
    values = [v for v in values if v is not None]
    if len(values) < 5:
        return None, None
    return statistics.fmean(values), max(statistics.pstdev(values), floor)


def get_trends(start_date, end_date) -> dict:
    """Daily series with per-point anomaly flags (|z| above the configured sigma)."""
    sigma = _thresholds()["ANOMALY_SIGMA"]
    rows = daily_series(start_date, end_date)

    yield_mean, yield_std = _stats([float(r["yield_percent"]) for r in rows], YIELD_STD_FLOOR)
    down_mean, down_std = _stats([float(r["downtime_minutes"]) for r in rows], DOWNTIME_STD_FLOOR)

    series = []
    for row in rows:
        yld = float(row["yield_percent"])
        down = float(row["downtime_minutes"])
        yield_anomaly = bool(yield_std and abs(yld - yield_mean) > sigma * yield_std)
        downtime_anomaly = bool(down_std and down - down_mean > sigma * down_std)
        series.append({
            "production_date": row["production_date"],
            "cassava_inflow_tons": _num(row["cassava_inflow_tons"]),
            "starch_output_tons": _num(row["starch_output_tons"]),
            "yield_percent": _num(yld),
            "downtime_minutes": row["downtime_minutes"],
            "yield_anomaly": yield_anomaly,
            "downtime_anomaly": downtime_anomaly,
        })

    return {
        "start_date": start_date,
        "end_date": end_date,
        "series": series,
        "stats": {
            "yield_mean": _num(yield_mean),
            "yield_std": _num(yield_std),
            "downtime_mean": _num(down_mean),
            "downtime_std": _num(down_std),
            "yield_target": _thresholds()["YIELD_TARGET_PERCENT"],
        },
    }


def build_alerts(*, today, latest, recent_series, raw_stock) -> list[dict]:
    t = _thresholds()
    alerts = []

    def add(severity, code, title, message):
        alerts.append({"severity": severity, "code": code, "title": title, "message": message})

    if latest is None:
        add("info", "NO_DATA", "No production data", "Record the first production entry to start tracking KPIs.")
        return alerts

    days_since = (today - latest.production_date).days
    if days_since >= t["STALE_DATA_DAYS"]:
        add("warning", "STALE_DATA", "Production data is stale",
            f"The last production entry is from {latest.production_date:%d %b %Y} ({days_since} days ago).")

    latest_yield = float(latest.yield_percent)
    if latest_yield > t["YIELD_MAX_PLAUSIBLE_PERCENT"]:
        add("warning", "IMPLAUSIBLE_YIELD", "Check production figures",
            f"Yield on {latest.production_date:%d %b} was {latest_yield:.1f}%, above the plausible maximum of "
            f"{t['YIELD_MAX_PLAUSIBLE_PERCENT']:g}%. The inflow or output figure may have been entered incorrectly.")
    elif latest_yield < t["YIELD_CRITICAL_PERCENT"]:
        add("critical", "LOW_YIELD", "Yield critically low",
            f"Yield on {latest.production_date:%d %b} was {latest_yield:.1f}%, below the {t['YIELD_CRITICAL_PERCENT']:g}% floor.")
    elif latest_yield < t["YIELD_TARGET_PERCENT"]:
        add("warning", "BELOW_TARGET_YIELD", "Yield below target",
            f"Yield on {latest.production_date:%d %b} was {latest_yield:.1f}% against a {t['YIELD_TARGET_PERCENT']:g}% target.")

    if latest.downtime_minutes >= t["DOWNTIME_CRITICAL_MINUTES"]:
        add("critical", "HIGH_DOWNTIME", "Severe downtime",
            f"{latest.downtime_minutes} minutes of downtime on {latest.production_date:%d %b}.")
    elif latest.downtime_minutes >= t["DOWNTIME_WARNING_MINUTES"]:
        add("warning", "ELEVATED_DOWNTIME", "Elevated downtime",
            f"{latest.downtime_minutes} minutes of downtime on {latest.production_date:%d %b}.")

    # Statistical anomalies against the plant's own recent history.
    history = [p for p in recent_series if p["production_date"] != latest.production_date]
    yield_mean, yield_std = _stats([p["yield_percent"] for p in history], YIELD_STD_FLOOR)
    if yield_std and abs(latest_yield - yield_mean) > t["ANOMALY_SIGMA"] * yield_std:
        direction = "above" if latest_yield > yield_mean else "below"
        add("warning", "YIELD_ANOMALY", "Unusual yield",
            f"Latest yield {latest_yield:.1f}% is well {direction} the {settings.PLATFORM_SETTINGS['TREND_WINDOW_DAYS']}-day average of {yield_mean:.1f}% — check measurement or process.")

    # Raw material cover: how many days of production the current stock supports.
    consumption = [p["cassava_inflow_tons"] for p in recent_series[-settings.PLATFORM_SETTINGS["STOCK_COVER_BASIS_DAYS"]:]]
    avg_daily_use = statistics.fmean(consumption) if consumption else 0
    if avg_daily_use > 0:
        cover_days = float(raw_stock) / avg_daily_use
        if cover_days < t["STOCK_COVER_CRITICAL_DAYS"]:
            add("critical", "RAW_STOCK_CRITICAL", "Raw cassava nearly exhausted",
                f"Stock covers about {cover_days:.1f} days of production at the current rate.")
        elif cover_days < t["STOCK_COVER_WARNING_DAYS"]:
            add("warning", "RAW_STOCK_LOW", "Raw cassava running low",
                f"Stock covers about {cover_days:.1f} days of production at the current rate.")

    alerts.sort(key=lambda a: SEVERITY_ORDER[a["severity"]])
    return alerts


def operational_health(alerts) -> str:
    severities = {a["severity"] for a in alerts}
    if "critical" in severities:
        return "critical"
    if "warning" in severities:
        return "attention"
    return "healthy"


def get_dashboard_snapshot() -> dict:
    today = timezone.localdate()
    latest = latest_entry()
    balances = {b.item.code: b.quantity_on_hand for b in InventoryBalance.objects.select_related("item")}
    raw_stock = balances.get(RAW_CASSAVA_CODE, Decimal("0"))
    starch_stock = balances.get(FINISHED_STARCH_CODE, Decimal("0"))

    windows = settings.PLATFORM_SETTINGS
    trend_start = today - timedelta(days=windows["TREND_WINDOW_DAYS"] - 1)
    trends = get_trends(trend_start, today)
    recent = trends["series"]

    # Recent window compared with the equal-length window before it.
    week = get_period_summary(today - timedelta(days=windows["COMPARISON_WINDOW_DAYS"] - 1), today, period="recent")

    basis = [p["cassava_inflow_tons"] for p in recent[-windows["STOCK_COVER_BASIS_DAYS"]:]]
    avg_daily_use = statistics.fmean(basis) if basis else 0
    alerts = build_alerts(today=today, latest=latest, recent_series=recent, raw_stock=raw_stock)

    return {
        "snapshot_date": latest.production_date if latest else None,
        "latest_inflow": _num(latest.cassava_inflow_tons) if latest else 0,
        "latest_output": _num(latest.starch_output_tons) if latest else 0,
        "latest_yield": _num(latest.yield_percent) if latest else 0,
        "latest_downtime": latest.downtime_minutes if latest else 0,
        "raw_cassava_stock": _num(raw_stock),
        "finished_starch_stock": _num(starch_stock),
        "raw_stock_cover_days": _num(float(raw_stock) / avg_daily_use, 1) if avg_daily_use else None,
        "week": {
            "start_date": week["start_date"],
            "end_date": week["end_date"],
            "summary": {k: week[k] for k in ("total_inflow", "total_output", "yield_percent", "total_downtime", "entries_count")},
            "comparison": week["comparison"],
        },
        # The dashboard's own trend series, so it needs one request, not two.
        "trends": trends,
        "alerts": alerts,
        "health": operational_health(alerts),
        "thresholds": {
            "yield_target": _thresholds()["YIELD_TARGET_PERCENT"],
            "yield_critical": _thresholds()["YIELD_CRITICAL_PERCENT"],
        },
        "generated_at": timezone.now(),
    }


def get_platform_config() -> dict:
    """Everything the UI needs to render thresholds, limits and labels — no client-side constants."""
    t = _thresholds()
    p = settings.PLATFORM_SETTINGS
    password_min = next(
        (v.get("OPTIONS", {}).get("min_length", 8) for v in settings.AUTH_PASSWORD_VALIDATORS
         if v["NAME"].endswith("MinimumLengthValidator")),
        8,
    )
    return {
        "server_date": timezone.localdate(),
        "timezone": settings.TIME_ZONE,
        "thresholds": {
            "yield_target_percent": t["YIELD_TARGET_PERCENT"],
            "yield_critical_percent": t["YIELD_CRITICAL_PERCENT"],
            "yield_max_plausible_percent": t["YIELD_MAX_PLAUSIBLE_PERCENT"],
            "downtime_warning_minutes": t["DOWNTIME_WARNING_MINUTES"],
            "downtime_critical_minutes": t["DOWNTIME_CRITICAL_MINUTES"],
            "stock_cover_warning_days": t["STOCK_COVER_WARNING_DAYS"],
            "stock_cover_critical_days": t["STOCK_COVER_CRITICAL_DAYS"],
            "stale_data_days": t["STALE_DATA_DAYS"],
            "anomaly_sigma": t["ANOMALY_SIGMA"],
        },
        "windows": {
            "trend_days": p["TREND_WINDOW_DAYS"],
            "comparison_days": p["COMPARISON_WINDOW_DAYS"],
            "stock_cover_basis_days": p["STOCK_COVER_BASIS_DAYS"],
        },
        "limits": {
            "max_range_days": p["MAX_RANGE_DAYS"],
            "max_downtime_minutes": p["MAX_DOWNTIME_MINUTES"],
            "reason_min_length": p["REASON_MIN_LENGTH"],
            "reason_max_length": p["REASON_MAX_LENGTH"],
            "password_min_length": password_min,
        },
        "periods": PERIOD_DEFINITIONS,
        "live_refresh_seconds": p["LIVE_REFRESH_SECONDS"],
    }
