from django.urls import path

from .views import (
    InventoryBalanceListView,
    InventoryItemListView,
    InventoryTransactionListView,
    ManualAdjustmentView,
    ReconciliationView,
)

urlpatterns = [
    path("items/", InventoryItemListView.as_view(), name="inventory-items"),
    path("balances/", InventoryBalanceListView.as_view(), name="inventory-balances"),
    path("transactions/", InventoryTransactionListView.as_view(), name="inventory-transactions"),
    path("adjustments/", ManualAdjustmentView.as_view(), name="inventory-adjustments"),
    path("reconciliation/", ReconciliationView.as_view(), name="inventory-reconciliation"),
]
