from django.contrib import admin

from common.admin import ReadOnlyModelAdmin

from .models import ProductionEntry


@admin.register(ProductionEntry)
class ProductionEntryAdmin(ReadOnlyModelAdmin):
    """Read-only: create and void entries through the API so stock stays in sync."""

    list_display = (
        "production_date", "cassava_inflow_tons", "starch_output_tons",
        "yield_percent", "downtime_minutes", "is_voided", "created_by",
    )
    search_fields = ("notes", "created_by__username")
    list_filter = ("is_voided", "production_date")
    list_select_related = ("created_by",)
