import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from common.validators import validate_non_negative_decimal


class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    contact_person = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SupplierDeliveryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_voided=False)


class SupplierDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="deliveries")
    delivery_date = models.DateField()
    quantity_tons = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_non_negative_decimal])
    quality_notes = models.TextField(blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="supplier_deliveries")

    is_voided = models.BooleanField(default=False)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="voided_supplier_deliveries",
    )
    void_reason = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SupplierDeliveryQuerySet.as_manager()

    class Meta:
        ordering = ["-delivery_date", "-created_at"]
        indexes = [
            models.Index(fields=["supplier", "delivery_date"], name="delivery_supplier_date_idx"),
            models.Index(fields=["delivery_date"], name="delivery_date_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(quantity_tons__gt=0), name="delivery_quantity_positive"),
        ]

    def __str__(self) -> str:
        return f"{self.supplier.name} - {self.quantity_tons} tons"
