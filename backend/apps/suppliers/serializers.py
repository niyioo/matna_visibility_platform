from django.utils import timezone
from rest_framework import serializers

from .models import Supplier, SupplierDelivery
from .services import create_supplier_delivery


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id", "name", "contact_person", "phone", "address",
            "is_active", "notes", "created_at", "updated_at",
        ]
        read_only_fields = fields


class SupplierWriteSerializer(serializers.ModelSerializer):
    """Create and update. `is_active` is only honoured on update (deactivate / reactivate)."""

    name = serializers.CharField(max_length=150, trim_whitespace=True)

    class Meta:
        model = Supplier
        fields = ["id", "name", "contact_person", "phone", "address", "notes", "is_active"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        duplicates = Supplier.objects.filter(name__iexact=value)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("A supplier with this name already exists.")
        return value

    def create(self, validated_data):
        validated_data.pop("is_active", None)
        return super().create(validated_data)

    def to_representation(self, instance):
        return SupplierSerializer(instance, context=self.context).data


class SupplierDeliverySerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    received_by_name = serializers.CharField(source="received_by.username", read_only=True)
    voided_by_name = serializers.CharField(source="voided_by.username", read_only=True, default=None)

    class Meta:
        model = SupplierDelivery
        fields = [
            "id", "supplier", "supplier_name", "delivery_date", "quantity_tons",
            "quality_notes", "vehicle_number", "received_by", "received_by_name",
            "is_voided", "voided_at", "voided_by_name", "void_reason",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class SupplierDeliveryCreateSerializer(serializers.ModelSerializer):
    quantity_tons = serializers.DecimalField(max_digits=10, decimal_places=2)
    quality_notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    vehicle_number = serializers.CharField(required=False, allow_blank=True, max_length=50)

    class Meta:
        model = SupplierDelivery
        fields = ["id", "supplier", "delivery_date", "quantity_tons", "quality_notes", "vehicle_number"]
        read_only_fields = ["id"]

    def validate_delivery_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Delivery date cannot be in the future.")
        return value

    def validate_quantity_tons(self, value):
        if value <= 0:
            raise serializers.ValidationError("Delivery quantity must be greater than zero.")
        return value

    def validate_supplier(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Cannot record a delivery for an inactive supplier.")
        return value

    def create(self, validated_data):
        return create_supplier_delivery(user=self.context["request"].user, **validated_data)

    def to_representation(self, instance):
        return SupplierDeliverySerializer(instance, context=self.context).data
