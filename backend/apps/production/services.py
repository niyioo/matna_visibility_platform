import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.inventory.models import InventoryReferenceType, InventoryTransactionType
from apps.inventory.services import (
    get_finished_starch_item,
    get_raw_cassava_item,
    lock_balances,
    record_inventory_transaction,
    reverse_reference,
)
from common.exceptions import AlreadyVoidedError, BusinessLogicError, DuplicateEntryError

from .models import ProductionEntry

logger = logging.getLogger(__name__)


def create_production_entry(
    *,
    user,
    production_date,
    cassava_inflow_tons,
    starch_output_tons,
    downtime_minutes,
    notes="",
):
    """
    Records a day's production and its stock movements atomically:
    raw cassava OUT (consumed) and finished starch IN (produced).
    """
    try:
        with transaction.atomic():
            raw_cassava_item = get_raw_cassava_item()
            finished_starch_item = get_finished_starch_item()
            lock_balances([raw_cassava_item, finished_starch_item])

            entry = ProductionEntry.objects.create(
                production_date=production_date,
                cassava_inflow_tons=cassava_inflow_tons,
                starch_output_tons=starch_output_tons,
                downtime_minutes=downtime_minutes,
                notes=notes,
                created_by=user,
            )

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

            if starch_output_tons > 0:
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
    except IntegrityError as exc:
        # Two clerks submitting the same day concurrently: the partial unique
        # constraint lets exactly one win.
        if ProductionEntry.objects.active().filter(production_date=production_date).exists():
            raise DuplicateEntryError(
                f"A production entry for {production_date} already exists. Void it first to correct it."
            ) from exc
        raise

    logger.info("Production entry %s created for %s by %s", entry.id, production_date, user.username)
    return entry


@transaction.atomic
def void_production_entry(*, entry_id, user, reason: str) -> ProductionEntry:
    """
    Voids an entry and reverses its stock movements. The entry is kept for audit;
    a corrected entry for the same date can then be recorded.
    """
    if not reason or not reason.strip():
        raise BusinessLogicError("A reason is required to void a production entry.")

    entry = ProductionEntry.objects.select_for_update().get(pk=entry_id)
    if entry.is_voided:
        raise AlreadyVoidedError()

    reverse_reference(
        reference_type=InventoryReferenceType.PRODUCTION_ENTRY,
        reference_id=entry.id,
        user=user,
        reason=f"production entry {entry.production_date} voided — {reason.strip()}",
    )

    entry.is_voided = True
    entry.voided_at = timezone.now()
    entry.voided_by = user
    entry.void_reason = reason.strip()
    entry.updated_by = user
    entry.save(update_fields=["is_voided", "voided_at", "voided_by", "void_reason", "updated_by", "updated_at"])

    logger.warning("Production entry %s (%s) voided by %s: %s", entry.id, entry.production_date, user.username, reason)
    return entry
