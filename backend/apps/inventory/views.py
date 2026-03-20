from rest_framework import generics
from common.permissions import IsAdminOrReadOnly
from .models import InventoryItem, InventoryBalance, InventoryTransaction
from .serializers import (
    InventoryItemSerializer,
    InventoryBalanceSerializer,
    InventoryTransactionSerializer,
)


class InventoryItemListView(generics.ListAPIView):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAdminOrReadOnly]


class InventoryBalanceListView(generics.ListAPIView):
    queryset = InventoryBalance.objects.select_related("item").all()
    serializer_class = InventoryBalanceSerializer
    permission_classes = [IsAdminOrReadOnly]


class InventoryTransactionListView(generics.ListAPIView):
    queryset = InventoryTransaction.objects.select_related("item", "created_by").all()
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["item__code", "transaction_type", "reference_type", "transaction_date"]
    search_fields = ["item__name", "item__code", "notes"]
    ordering_fields = ["transaction_date", "created_at", "quantity"]