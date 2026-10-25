import django_filters
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrOperations, IsAdminRole, IsAnyOperationalRole
from common.serializers import VoidSerializer

from .models import ProductionEntry
from .serializers import ProductionEntryCreateSerializer, ProductionEntrySerializer
from .services import void_production_entry


class ProductionEntryFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="production_date", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="production_date", lookup_expr="lte")

    class Meta:
        model = ProductionEntry
        fields = ["production_date", "is_voided"]


class ProductionEntryListCreateView(generics.ListCreateAPIView):
    """Lists live entries by default; pass ?is_voided=true to audit voided ones."""

    filterset_class = ProductionEntryFilter
    search_fields = ["notes", "created_by__username"]
    ordering_fields = ["production_date", "yield_percent", "downtime_minutes", "created_at"]

    def get_queryset(self):
        queryset = ProductionEntry.objects.select_related("created_by", "updated_by", "voided_by")
        if "is_voided" not in self.request.query_params:
            queryset = queryset.active()
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductionEntryCreateSerializer
        return ProductionEntrySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminOrOperations()]
        return [IsAnyOperationalRole()]


class ProductionEntryDetailView(generics.RetrieveAPIView):
    queryset = ProductionEntry.objects.select_related("created_by", "updated_by", "voided_by")
    serializer_class = ProductionEntrySerializer
    permission_classes = [IsAnyOperationalRole]


class ProductionEntryVoidView(APIView):
    """POST {reason} — admin only. Reverses the entry's stock movements."""

    permission_classes = [IsAdminRole]

    def post(self, request, pk):
        generics.get_object_or_404(ProductionEntry, pk=pk)
        serializer = VoidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = void_production_entry(entry_id=pk, user=request.user, reason=serializer.validated_data["reason"])
        return Response(ProductionEntrySerializer(entry).data, status=status.HTTP_200_OK)
