from django.contrib import admin
from .models import InventoryItem, InventoryBalance, InventoryTransaction


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "item_type", "unit", "is_active")
    search_fields = ("code", "name")
    list_filter = ("item_type", "is_active")


@admin.register(InventoryBalance)
class InventoryBalanceAdmin(admin.ModelAdmin):
    list_display = ("item", "quantity_on_hand", "last_updated_at")


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("item", "transaction_type", "quantity", "reference_type", "transaction_date", "created_by")
    list_filter = ("transaction_type", "reference_type", "transaction_date")
    search_fields = ("item__name", "item__code", "notes")