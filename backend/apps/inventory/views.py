import django_filters
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminRole, IsAnyOperationalRole

from .models import InventoryBalance, InventoryItem, InventoryTransaction
from .reconciliation import reconcile_inventory
from .serializers import (
    InventoryBalanceSerializer,
    InventoryItemSerializer,
    InventoryTransactionSerializer,
    ManualAdjustmentSerializer,
)
from .services import post_manual_adjustment


class InventoryItemListView(generics.ListAPIView):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAnyOperationalRole]
    pagination_class = None


class InventoryBalanceListView(generics.ListAPIView):
    queryset = InventoryBalance.objects.select_related("item").order_by("item__name")
    serializer_class = InventoryBalanceSerializer
    permission_classes = [IsAnyOperationalRole]
    pagination_class = None


class InventoryTransactionFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="transaction_date", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="transaction_date", lookup_expr="lte")
    item_code = django_filters.CharFilter(field_name="item__code")

    class Meta:
        model = InventoryTransaction
        fields = ["transaction_type", "reference_type", "reference_id", "transaction_date"]


class InventoryTransactionListView(generics.ListAPIView):
    queryset = InventoryTransaction.objects.select_related("item", "created_by", "reversed_by")
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsAnyOperationalRole]
    filterset_class = InventoryTransactionFilter
    search_fields = ["item__name", "item__code", "notes"]
    ordering_fields = ["transaction_date", "created_at", "quantity"]


class ManualAdjustmentView(APIView):
    """POST — admin-only stock-count correction, recorded in the ledger with a reason."""

    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = ManualAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        tx = post_manual_adjustment(
            item=data["item"],
            direction=data["direction"],
            quantity=data["quantity"],
            reason=data["reason"],
            user=request.user,
            transaction_date=data.get("transaction_date"),
        )
        return Response(InventoryTransactionSerializer(tx).data, status=status.HTTP_201_CREATED)


class ReconciliationView(APIView):
    """GET — admin-only integrity report comparing balances, ledger and documents."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response(reconcile_inventory())
