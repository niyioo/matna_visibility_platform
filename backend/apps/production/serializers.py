from rest_framework import serializers
from .models import ProductionEntry
from .services import create_production_entry


class ProductionEntrySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    updated_by_name = serializers.CharField(source="updated_by.username", read_only=True)

    class Meta:
        model = ProductionEntry
        fields = [
            "id", "production_date", "cassava_inflow_tons", "starch_output_tons",
            "downtime_minutes", "yield_percent", "notes",
            "created_by", "created_by_name", "updated_by", "updated_by_name",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "yield_percent", "created_by", "updated_by", "created_at", "updated_at"
        ]


class ProductionEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionEntry
        fields = [
            "id", "production_date", "cassava_inflow_tons",
            "starch_output_tons", "downtime_minutes", "notes"
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        inflow = attrs.get("cassava_inflow_tons")
        output = attrs.get("starch_output_tons")

        if inflow == 0 and output > 0:
            raise serializers.ValidationError("Starch output cannot be greater than 0 when cassava inflow is 0.")

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return create_production_entry(user=user, **validated_data)