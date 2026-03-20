from rest_framework import serializers
from .models import Supplier, SupplierDelivery
from .services import create_supplier_delivery


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class SupplierDeliverySerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    received_by_name = serializers.CharField(source="received_by.username", read_only=True)

    class Meta:
        model = SupplierDelivery
        fields = [
            "id", "supplier", "supplier_name", "delivery_date", "quantity_tons",
            "quality_notes", "vehicle_number", "received_by", "received_by_name",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "received_by", "created_at", "updated_at"]


class SupplierDeliveryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierDelivery
        fields = ["id", "supplier", "delivery_date", "quantity_tons", "quality_notes", "vehicle_number"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        user = self.context["request"].user
        return create_supplier_delivery(user=user, **validated_data)