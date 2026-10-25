import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from common.utils import quantize_two_places
from common.validators import validate_non_negative_decimal


class ProductionEntryQuerySet(models.QuerySet):
    def active(self):
        """Entries that count towards stock and KPIs (voided ones are kept for audit only)."""
        return self.filter(is_voided=False)


class ProductionEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    production_date = models.DateField()
    cassava_inflow_tons = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_non_negative_decimal])
    starch_output_tons = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_non_negative_decimal])
    downtime_minutes = models.PositiveIntegerField(default=0)
    yield_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True, null=True)

    is_voided = models.BooleanField(default=False)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="voided_production_entries",
    )
    void_reason = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_production_entries")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="updated_production_entries", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductionEntryQuerySet.as_manager()

    class Meta:
        ordering = ["-production_date", "-created_at"]
        indexes = [
            models.Index(fields=["is_voided", "production_date"], name="prod_active_date_idx"),
        ]
        constraints = [
            # One live entry per day; voided entries don't block a corrected re-entry.
            models.UniqueConstraint(
                fields=["production_date"],
                condition=Q(is_voided=False),
                name="prod_unique_active_date",
            ),
            models.CheckConstraint(condition=Q(cassava_inflow_tons__gt=0), name="prod_inflow_positive"),
            models.CheckConstraint(condition=Q(starch_output_tons__gte=0), name="prod_output_non_negative"),
            models.CheckConstraint(
                condition=Q(starch_output_tons__lte=F("cassava_inflow_tons")),
                name="prod_output_lte_inflow",
            ),
        ]

    def __str__(self) -> str:
        return f"Production Entry - {self.production_date}{' (voided)' if self.is_voided else ''}"

    def calculate_yield(self) -> Decimal:
        if self.cassava_inflow_tons and self.cassava_inflow_tons > 0:
            return quantize_two_places((self.starch_output_tons / self.cassava_inflow_tons) * Decimal("100"))
        return Decimal("0.00")

    def save(self, *args, **kwargs):
        self.yield_percent = self.calculate_yield()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "yield_percent" not in update_fields:
            kwargs["update_fields"] = list(update_fields) + ["yield_percent"]
        super().save(*args, **kwargs)
