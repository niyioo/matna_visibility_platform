from django.contrib import admin
from .models import ProductionEntry


@admin.register(ProductionEntry)
class ProductionEntryAdmin(admin.ModelAdmin):
    list_display = (
        "production_date", "cassava_inflow_tons", "starch_output_tons",
        "yield_percent", "downtime_minutes", "created_by"
    )
    search_fields = ("notes", "created_by__username")
    list_filter = ("production_date",)