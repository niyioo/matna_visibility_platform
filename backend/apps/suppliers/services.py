from django.db import transaction
from apps.inventory.services import get_raw_cassava_item, record_inventory_transaction
from apps.inventory.models import InventoryTransactionType, InventoryReferenceType
from .models import SupplierDelivery


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

    raw_cassava_item = get_raw_cassava_item()

    record_inventory_transaction(
        item=raw_cassava_item,
        transaction_type=InventoryTransactionType.IN,
        quantity=quantity_tons,
        reference_type=InventoryReferenceType.SUPPLIER_DELIVERY,
        reference_id=delivery.id,
        transaction_date=delivery.delivery_date,
        created_by=user,
        notes=f"Supplier delivery from {supplier.name}",
    )

    return delivery