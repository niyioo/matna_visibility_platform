from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from common.serializers import reason_field

from .models import InventoryBalance, InventoryItem, InventoryTransaction, InventoryTransactionType


class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ["id", "code", "name", "unit", "item_type", "is_active"]
        read_only_fields = fields


class InventoryBalanceSerializer(serializers.ModelSerializer):
    item = InventoryItemSerializer(read_only=True)

    class Meta:
        model = InventoryBalance
        fields = ["id", "item", "quantity_on_hand", "last_updated_at"]
        read_only_fields = fields


class InventoryTransactionSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_code = serializers.CharField(source="item.code", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    is_reversal = serializers.BooleanField(read_only=True)
    is_reversed = serializers.SerializerMethodField()

    class Meta:
        model = InventoryTransaction
        fields = [
            "id", "item", "item_name", "item_code", "transaction_type", "quantity",
            "balance_after", "reference_type", "reference_id", "transaction_date", "notes",
            "reversal_of", "is_reversal", "is_reversed",
            "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = fields

    def get_is_reversed(self, obj):
        return hasattr(obj, "reversed_by")


class ManualAdjustmentSerializer(serializers.Serializer):
    item_code = serializers.SlugRelatedField(
        slug_field="code", queryset=InventoryItem.objects.filter(is_active=True), source="item"
    )
    direction = serializers.ChoiceField(choices=[InventoryTransactionType.IN, InventoryTransactionType.OUT])
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    reason = reason_field()
    transaction_date = serializers.DateField(required=False)

    def validate_transaction_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Adjustment date cannot be in the future.")
        return value
