from rest_framework import serializers
from .models import InventoryItem, InventoryBalance, InventoryTransaction


class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = "__all__"


class InventoryBalanceSerializer(serializers.ModelSerializer):
    item = InventoryItemSerializer(read_only=True)

    class Meta:
        model = InventoryBalance
        fields = ["id", "item", "quantity_on_hand", "last_updated_at"]


class InventoryTransactionSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_code = serializers.CharField(source="item.code", read_only=True)
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = InventoryTransaction
        fields = [
            "id", "item", "item_name", "item_code", "transaction_type", "quantity",
            "reference_type", "reference_id", "transaction_date", "notes",
            "created_by", "created_by_name", "created_at"
        ]
        read_only_fields = ["id", "created_at"]