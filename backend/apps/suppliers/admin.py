from django.contrib import admin
from .models import Supplier, SupplierDelivery


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "is_active", "created_at")
    search_fields = ("name", "contact_person", "phone")
    list_filter = ("is_active",)


@admin.register(SupplierDelivery)
class SupplierDeliveryAdmin(admin.ModelAdmin):
    list_display = ("supplier", "delivery_date", "quantity_tons", "received_by", "created_at")
    search_fields = ("supplier__name", "vehicle_number", "quality_notes")
    list_filter = ("delivery_date",)