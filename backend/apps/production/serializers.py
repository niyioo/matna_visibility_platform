from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from .models import ProductionEntry
from .services import create_production_entry

MAX_DOWNTIME_MINUTES = settings.PLATFORM_SETTINGS["MAX_DOWNTIME_MINUTES"]


class ProductionEntrySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    updated_by_name = serializers.CharField(source="updated_by.username", read_only=True, default=None)
    voided_by_name = serializers.CharField(source="voided_by.username", read_only=True, default=None)

    class Meta:
        model = ProductionEntry
        fields = [
            "id", "production_date", "cassava_inflow_tons", "starch_output_tons",
            "downtime_minutes", "yield_percent", "notes",
            "is_voided", "voided_at", "voided_by_name", "void_reason",
            "created_by", "created_by_name", "updated_by", "updated_by_name",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class ProductionEntryCreateSerializer(serializers.ModelSerializer):
    # Declared explicitly so our own duplicate-date check (with guidance on how
    # to correct an entry) replaces DRF's generic auto-generated unique message.
    production_date = serializers.DateField()
    cassava_inflow_tons = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0"))
    starch_output_tons = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0"))
    downtime_minutes = serializers.IntegerField(min_value=0, max_value=MAX_DOWNTIME_MINUTES)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    class Meta:
        model = ProductionEntry
        fields = [
            "id", "production_date", "cassava_inflow_tons",
            "starch_output_tons", "downtime_minutes", "notes",
        ]
        read_only_fields = ["id"]

    def validate_production_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Production date cannot be in the future.")
        if ProductionEntry.objects.active().filter(production_date=value).exists():
            raise serializers.ValidationError(
                "An entry for this date already exists. Void it first if it needs correcting."
            )
        return value

    def validate_cassava_inflow_tons(self, value):
        if value <= 0:
            raise serializers.ValidationError("Cassava inflow must be greater than zero.")
        return value

    def validate(self, attrs):
        if attrs["starch_output_tons"] > attrs["cassava_inflow_tons"]:
            raise serializers.ValidationError(
                {"starch_output_tons": "Starch output cannot exceed cassava inflow (yield cannot exceed 100%)."}
            )
        return attrs

    def create(self, validated_data):
        return create_production_entry(user=self.context["request"].user, **validated_data)

    def to_representation(self, instance):
        return ProductionEntrySerializer(instance, context=self.context).data

