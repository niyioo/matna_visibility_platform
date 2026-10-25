import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q

from common.validators import validate_non_negative_decimal


class InventoryItemType(models.TextChoices):
    RAW_MATERIAL = "RAW_MATERIAL", "Raw Material"
    FINISHED_GOOD = "FINISHED_GOOD", "Finished Good"


class InventoryTransactionType(models.TextChoices):
    IN = "IN", "In"
    OUT = "OUT", "Out"
    # Legacy: positive-only adjustment. New corrections use IN/OUT with
    # reference_type=MANUAL_ADJUSTMENT so the direction is explicit.
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
    """Cached running total of the ledger. Only `record_inventory_transaction` writes it."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.OneToOneField(InventoryItem, on_delete=models.PROTECT, related_name="balance")
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[validate_non_negative_decimal])
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["item__name"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity_on_hand__gte=0), name="inv_balance_non_negative"),
        ]

    def __str__(self) -> str:
        return f"{self.item.name}: {self.quantity_on_hand}"


class ImmutableRecordError(Exception):
    pass


class InventoryTransaction(models.Model):
    """
    Append-only stock ledger. Rows are never edited or deleted; mistakes are
    corrected by posting a reversal (`reversal_of`) that moves stock back.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=InventoryTransactionType.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_non_negative_decimal])
    reference_type = models.CharField(max_length=30, choices=InventoryReferenceType.choices)
    reference_id = models.UUIDField()
    transaction_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    reversal_of = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reversed_by",
        help_text="The transaction this entry cancels out. A transaction can be reversed at most once.",
    )
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inventory_transactions")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["item", "transaction_date"], name="inv_tx_item_date_idx"),
            models.Index(fields=["reference_type", "reference_id"], name="inv_tx_ref_idx"),
            models.Index(fields=["transaction_type"], name="inv_tx_type_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="inv_tx_quantity_positive"),
        ]

    def __str__(self) -> str:
        return f"{self.item.code} - {self.transaction_type} - {self.quantity}"

    @property
    def signed_quantity(self) -> Decimal:
        return -self.quantity if self.transaction_type == InventoryTransactionType.OUT else self.quantity

    @property
    def is_reversal(self) -> bool:
        return self.reversal_of_id is not None

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ImmutableRecordError("Inventory transactions are immutable; post a reversal instead.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableRecordError("Inventory transactions cannot be deleted; post a reversal instead.")
