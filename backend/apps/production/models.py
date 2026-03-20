import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from common.validators import validate_non_negative_decimal, validate_non_negative_integer
from common.utils import quantize_two_places


class ProductionEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    production_date = models.DateField(unique=True)
    cassava_inflow_tons = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_non_negative_decimal])
    starch_output_tons = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_non_negative_decimal])
    downtime_minutes = models.PositiveIntegerField(default=0)
    yield_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_production_entries")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="updated_production_entries", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-production_date", "-created_at"]

    def __str__(self) -> str:
        return f"Production Entry - {self.production_date}"

    def calculate_yield(self) -> Decimal:
        if self.cassava_inflow_tons and self.cassava_inflow_tons > 0:
            return quantize_two_places((self.starch_output_tons / self.cassava_inflow_tons) * Decimal("100"))
        return Decimal("0.00")

    def save(self, *args, **kwargs):
        self.yield_percent = self.calculate_yield()
        super().save(*args, **kwargs)