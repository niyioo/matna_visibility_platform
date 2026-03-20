from rest_framework import generics
from common.permissions import IsAdminOrOperations, IsAdminOrReadOnly
from .models import Supplier, SupplierDelivery
from .serializers import SupplierSerializer, SupplierDeliverySerializer, SupplierDeliveryCreateSerializer


class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name", "contact_person", "phone"]
    ordering_fields = ["name", "created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminOrOperations()]
        return [IsAdminOrReadOnly()]


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminOrOperations]


class SupplierDeliveryListCreateView(generics.ListCreateAPIView):
    queryset = SupplierDelivery.objects.select_related("supplier", "received_by").all()
    filterset_fields = ["supplier", "delivery_date"]
    search_fields = ["supplier__name", "vehicle_number", "quality_notes"]
    ordering_fields = ["delivery_date", "created_at", "quantity_tons"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SupplierDeliveryCreateSerializer
        return SupplierDeliverySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminOrOperations()]
        return [IsAdminOrReadOnly()]


class SupplierDeliveryDetailView(generics.RetrieveAPIView):
    queryset = SupplierDelivery.objects.select_related("supplier", "received_by").all()
    serializer_class = SupplierDeliverySerializer
    permission_classes = [IsAdminOrReadOnly]