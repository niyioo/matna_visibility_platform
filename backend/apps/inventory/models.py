import uuid
from django.conf import settings
from django.db import models
from common.validators import validate_non_negative_decimal


class InventoryItemType(models.TextChoices):
    RAW_MATERIAL = "RAW_MATERIAL", "Raw Material"
    FINISHED_GOOD = "FINISHED_GOOD", "Finished Good"


class InventoryTransactionType(models.TextChoices):
    IN = "IN", "In"
    OUT = "OUT", "Out"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"


class InventoryReferenceType(models.TextChoices):
    SUPPLIER_DELIVERY = "SUPPLIER_DELIVERY", "Supplier Delivery"
    PRODUCTION_ENTRY = "PRODUCTION_ENTRY", "Production Entry"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT", "Manual Adjustment"


class InventoryItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, default="tons")
    item_type = models.CharField(max_length=30, choices=InventoryItemType.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class InventoryBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.OneToOneField(InventoryItem, on_delete=models.CASCADE, related_name="balance")
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[validate_non_negative_decimal])
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["item__name"]

    def __str__(self) -> str:
        return f"{self.item.name}: {self.quantity_on_hand}"


class InventoryTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=InventoryTransactionType.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_non_negative_decimal])
    reference_type = models.CharField(max_length=30, choices=InventoryReferenceType.choices)
    reference_id = models.UUIDField()
    transaction_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inventory_transactions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.item.code} - {self.transaction_type} - {self.quantity}"