from .models import InventoryBalance, InventoryTransaction


def get_inventory_balances():
    return InventoryBalance.objects.select_related("item").all().order_by("item__name")


def get_inventory_transactions():
    return InventoryTransaction.objects.select_related("item", "created_by").all()