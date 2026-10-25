from django.contrib import admin

from common.admin import ReadOnlyModelAdmin

from .models import InventoryBalance, InventoryItem, InventoryTransaction


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "item_type", "unit", "is_active")
    search_fields = ("code", "name")
    list_filter = ("item_type", "is_active")
    readonly_fields = ("code",)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InventoryBalance)
class InventoryBalanceAdmin(ReadOnlyModelAdmin):
    list_display = ("item", "quantity_on_hand", "last_updated_at")


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(ReadOnlyModelAdmin):
    list_display = ("transaction_date", "item", "transaction_type", "quantity", "balance_after", "reference_type", "reversal_of", "created_by")
    list_filter = ("transaction_type", "reference_type", "transaction_date")
    search_fields = ("item__name", "item__code", "notes", "reference_id")
    list_select_related = ("item", "created_by")
