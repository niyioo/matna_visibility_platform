import django_filters
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrOperations, IsAdminRole, IsAnyOperationalRole
from common.serializers import VoidSerializer

from .models import Supplier, SupplierDelivery
from .serializers import (
    SupplierDeliveryCreateSerializer,
    SupplierDeliverySerializer,
    SupplierSerializer,
    SupplierWriteSerializer,
)
from .services import void_supplier_delivery


class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all().order_by("name")
    filterset_fields = ["is_active"]
    search_fields = ["name", "contact_person", "phone"]
    ordering_fields = ["name", "created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SupplierWriteSerializer
        return SupplierSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminOrOperations()]
        return [IsAnyOperationalRole()]


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    DELETE deactivates the supplier rather than deleting it: deliveries reference
    suppliers and must keep their history.
    """

    queryset = Supplier.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return SupplierWriteSerializer
        return SupplierSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [IsAnyOperationalRole()]
        return [IsAdminOrOperations()]

    def destroy(self, request, *args, **kwargs):
        supplier = self.get_object()
        if supplier.is_active:
            supplier.is_active = False
            supplier.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class SupplierDeliveryFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="delivery_date", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="delivery_date", lookup_expr="lte")

    class Meta:
        model = SupplierDelivery
        fields = ["supplier", "delivery_date", "is_voided"]


class SupplierDeliveryListCreateView(generics.ListCreateAPIView):
    filterset_class = SupplierDeliveryFilter
    search_fields = ["supplier__name", "vehicle_number", "quality_notes"]
    ordering_fields = ["delivery_date", "created_at", "quantity_tons"]

    def get_queryset(self):
        queryset = SupplierDelivery.objects.select_related("supplier", "received_by", "voided_by")
        if "is_voided" not in self.request.query_params:
            queryset = queryset.active()
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SupplierDeliveryCreateSerializer
        return SupplierDeliverySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminOrOperations()]
        return [IsAnyOperationalRole()]


class SupplierDeliveryDetailView(generics.RetrieveAPIView):
    queryset = SupplierDelivery.objects.select_related("supplier", "received_by", "voided_by")
    serializer_class = SupplierDeliverySerializer
    permission_classes = [IsAnyOperationalRole]


class SupplierDeliveryVoidView(APIView):
    """POST {reason} — admin only. Removes the delivered cassava from stock."""

    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        generics.get_object_or_404(SupplierDelivery, pk=pk)
        serializer = VoidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delivery = void_supplier_delivery(delivery_id=pk, user=request.user, reason=serializer.validated_data["reason"])
        return Response(SupplierDeliverySerializer(delivery).data, status=status.HTTP_200_OK)
