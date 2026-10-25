from django.contrib import admin

from common.admin import ReadOnlyModelAdmin

from .models import Supplier, SupplierDelivery


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "is_active", "created_at")
    search_fields = ("name", "contact_person", "phone")
    list_filter = ("is_active",)

    def has_delete_permission(self, request, obj=None):
        return False  # deactivate instead; deliveries keep their supplier


@admin.register(SupplierDelivery)
class SupplierDeliveryAdmin(ReadOnlyModelAdmin):
    """Read-only: record and void deliveries through the API so stock stays in sync."""

    list_display = ("supplier", "delivery_date", "quantity_tons", "is_voided", "received_by", "created_at")
    search_fields = ("supplier__name", "vehicle_number", "quality_notes")
    list_filter = ("is_voided", "delivery_date")
    list_select_related = ("supplier", "received_by")
