from django.urls import path
from .views import InventoryItemListView, InventoryBalanceListView, InventoryTransactionListView

urlpatterns = [
    path("items/", InventoryItemListView.as_view(), name="inventory-items"),
    path("balances/", InventoryBalanceListView.as_view(), name="inventory-balances"),
    path("transactions/", InventoryTransactionListView.as_view(), name="inventory-transactions"),
]