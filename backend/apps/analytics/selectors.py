from apps.production.models import ProductionEntry


def _apply_date_filters(queryset, start_date=None, end_date=None):
    if start_date:
        queryset = queryset.filter(production_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(production_date__lte=end_date)
    return queryset


def get_yield_trend(start_date=None, end_date=None):
    queryset = ProductionEntry.objects.order_by("production_date")
    queryset = _apply_date_filters(queryset, start_date, end_date)
    return list(
        queryset.values("production_date", "yield_percent")
    )


def get_inflow_vs_output_trend(start_date=None, end_date=None):
    queryset = ProductionEntry.objects.order_by("production_date")
    queryset = _apply_date_filters(queryset, start_date, end_date)
    return list(
        queryset.values(
            "production_date",
            "cassava_inflow_tons",
            "starch_output_tons",
        )
    )


def get_downtime_trend(start_date=None, end_date=None):
    queryset = ProductionEntry.objects.order_by("production_date")
    queryset = _apply_date_filters(queryset, start_date, end_date)
    return list(
        queryset.values("production_date", "downtime_minutes")
    )