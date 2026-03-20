from django.db import transaction

from .models import ProductionEntry
from apps.inventory.services import (
    get_raw_cassava_item,
    get_finished_starch_item,
    record_inventory_transaction,
)
from apps.inventory.models import InventoryTransactionType, InventoryReferenceType


@transaction.atomic
def create_production_entry(
    *,
    user,
    production_date,
    cassava_inflow_tons,
    starch_output_tons,
    downtime_minutes,
    notes="",
):
    entry = ProductionEntry.objects.create(
        production_date=production_date,
        cassava_inflow_tons=cassava_inflow_tons,
        starch_output_tons=starch_output_tons,
        downtime_minutes=downtime_minutes,
        notes=notes,
        created_by=user,
    )

    raw_cassava_item = get_raw_cassava_item()
    finished_starch_item = get_finished_starch_item()

    record_inventory_transaction(
        item=raw_cassava_item,
        transaction_type=InventoryTransactionType.OUT,
        quantity=cassava_inflow_tons,
        reference_type=InventoryReferenceType.PRODUCTION_ENTRY,
        reference_id=entry.id,
        transaction_date=production_date,
        created_by=user,
        notes=f"Cassava consumed for production on {production_date}",
    )

    record_inventory_transaction(
        item=finished_starch_item,
        transaction_type=InventoryTransactionType.IN,
        quantity=starch_output_tons,
        reference_type=InventoryReferenceType.PRODUCTION_ENTRY,
        reference_id=entry.id,
        transaction_date=production_date,
        created_by=user,
        notes=f"Starch produced on {production_date}",
    )

    return entry