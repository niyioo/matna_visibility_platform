from rest_framework import generics
from common.permissions import IsAdminOrOperations, IsAdminOrReadOnly
from .models import ProductionEntry
from .serializers import ProductionEntrySerializer, ProductionEntryCreateSerializer


class ProductionEntryListCreateView(generics.ListCreateAPIView):
    queryset = ProductionEntry.objects.select_related("created_by", "updated_by").all()
    filterset_fields = ["production_date"]
    search_fields = ["notes", "created_by__username"]
    ordering_fields = ["production_date", "yield_percent", "downtime_minutes", "created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductionEntryCreateSerializer
        return ProductionEntrySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminOrOperations()]
        return [IsAdminOrReadOnly()]


class ProductionEntryDetailView(generics.RetrieveAPIView):
    queryset = ProductionEntry.objects.select_related("created_by", "updated_by").all()
    serializer_class = ProductionEntrySerializer
    permission_classes = [IsAdminOrReadOnly]