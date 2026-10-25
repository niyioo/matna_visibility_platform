import logging

from django.db import transaction
from django.utils import timezone

from apps.inventory.models import InventoryReferenceType, InventoryTransactionType
from apps.inventory.services import get_raw_cassava_item, record_inventory_transaction, reverse_reference
from common.exceptions import AlreadyVoidedError, BusinessLogicError

from .models import SupplierDelivery

logger = logging.getLogger(__name__)


@transaction.atomic
def create_supplier_delivery(*, user, supplier, delivery_date, quantity_tons, quality_notes="", vehicle_number=""):
    delivery = SupplierDelivery.objects.create(
        supplier=supplier,
        delivery_date=delivery_date,
        quantity_tons=quantity_tons,
        quality_notes=quality_notes,
        vehicle_number=vehicle_number,
        received_by=user,
    )

    record_inventory_transaction(
        item=get_raw_cassava_item(),
        transaction_type=InventoryTransactionType.IN,
        quantity=quantity_tons,
        reference_type=InventoryReferenceType.SUPPLIER_DELIVERY,
        reference_id=delivery.id,
        transaction_date=delivery.delivery_date,
        created_by=user,
        notes=f"Supplier delivery from {supplier.name}",
    )

    logger.info("Delivery %s: %s t from %s received by %s", delivery.id, quantity_tons, supplier.name, user.username)
    return delivery


@transaction.atomic
def void_supplier_delivery(*, delivery_id, user, reason: str) -> SupplierDelivery:
    """
    Voids a delivery and removes its cassava from stock. Fails with
    InsufficientStockError if that cassava has already been consumed — in that
    case the production entries that used it must be voided first.
    """
    if not reason or not reason.strip():
        raise BusinessLogicError("A reason is required to void a delivery.")

    delivery = SupplierDelivery.objects.select_for_update().select_related("supplier").get(pk=delivery_id)
    if delivery.is_voided:
        raise AlreadyVoidedError()

    reverse_reference(
        reference_type=InventoryReferenceType.SUPPLIER_DELIVERY,
        reference_id=delivery.id,
        user=user,
        reason=f"delivery from {delivery.supplier.name} on {delivery.delivery_date} voided — {reason.strip()}",
    )

    delivery.is_voided = True
    delivery.voided_at = timezone.now()
    delivery.voided_by = user
    delivery.void_reason = reason.strip()
    delivery.save(update_fields=["is_voided", "voided_at", "voided_by", "void_reason", "updated_at"])

    logger.warning("Delivery %s voided by %s: %s", delivery.id, user.username, reason)
    return delivery
