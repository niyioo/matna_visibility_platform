import logging
import uuid
from decimal import Decimal
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from common.constants import FINISHED_STARCH_CODE, RAW_CASSAVA_CODE
from common.exceptions import BusinessLogicError, InsufficientStockError

from .models import (
    InventoryBalance,
    InventoryItem,
    InventoryItemType,
    InventoryReferenceType,
    InventoryTransaction,
    InventoryTransactionType,
)

logger = logging.getLogger(__name__)

DEFAULT_ITEMS = {
    RAW_CASSAVA_CODE: {"name": "Raw Cassava", "item_type": InventoryItemType.RAW_MATERIAL},
    FINISHED_STARCH_CODE: {"name": "Finished Starch", "item_type": InventoryItemType.FINISHED_GOOD},
}

_OPPOSITE = {
    InventoryTransactionType.IN: InventoryTransactionType.OUT,
    InventoryTransactionType.OUT: InventoryTransactionType.IN,
    InventoryTransactionType.ADJUSTMENT: InventoryTransactionType.OUT,
}


# ── Items ────────────────────────────────────────────────────────────────────

def get_or_create_inventory_item(code: str, name: str, item_type: str, unit: str = "tons") -> InventoryItem:
    item, _ = InventoryItem.objects.get_or_create(
        code=code,
        defaults={"name": name, "item_type": item_type, "unit": unit},
    )
    InventoryBalance.objects.get_or_create(item=item, defaults={"quantity_on_hand": Decimal("0.00")})
    return item


def ensure_default_inventory_items() -> None:
    for code, attrs in DEFAULT_ITEMS.items():
        get_or_create_inventory_item(code=code, **attrs)


def get_item(code: str) -> InventoryItem:
    """One indexed query in the common case; seeds defaults on a fresh database."""
    try:
        return InventoryItem.objects.get(code=code)
    except InventoryItem.DoesNotExist:
        if code not in DEFAULT_ITEMS:
            raise
        return get_or_create_inventory_item(code=code, **DEFAULT_ITEMS[code])


def get_raw_cassava_item() -> InventoryItem:
    return get_item(RAW_CASSAVA_CODE)


def get_finished_starch_item() -> InventoryItem:
    return get_item(FINISHED_STARCH_CODE)


# ── Ledger ───────────────────────────────────────────────────────────────────

def lock_balances(items: Iterable[InventoryItem]) -> dict:
    """
    Row-lock the balances of `items` in a fixed order (by item code).

    Every multi-item stock operation calls this first, so two concurrent
    operations always acquire locks in the same order and cannot deadlock.
    Must be called inside a transaction.
    """
    items = sorted({item.pk: item for item in items}.values(), key=lambda i: i.code)
    for item in items:
        InventoryBalance.objects.get_or_create(item=item, defaults={"quantity_on_hand": Decimal("0.00")})
    locked = InventoryBalance.objects.select_for_update().filter(item__in=items).order_by("item__code")
    return {balance.item_id: balance for balance in locked}


@transaction.atomic
def record_inventory_transaction(
    *,
    item: InventoryItem,
    transaction_type: str,
    quantity: Decimal,
    reference_type: str,
    reference_id,
    transaction_date,
    created_by,
    notes: str = "",
    reversal_of: InventoryTransaction | None = None,
) -> InventoryTransaction:
    if quantity is None or Decimal(quantity) <= 0:
        raise BusinessLogicError("Inventory quantity must be greater than zero.")
    if transaction_type not in InventoryTransactionType.values:
        raise BusinessLogicError(f"Invalid transaction type: '{transaction_type}'.")

    balance = lock_balances([item])[item.pk]
    current = balance.quantity_on_hand
    delta = -quantity if transaction_type == InventoryTransactionType.OUT else quantity
    new_balance = current + delta

    if new_balance < 0:
        raise InsufficientStockError(
            f"Insufficient stock for '{item.name}'. "
            f"Available: {current} {item.unit}, requested: {quantity} {item.unit}."
        )

    tx = InventoryTransaction.objects.create(
        item=item,
        transaction_type=transaction_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        transaction_date=transaction_date,
        notes=notes,
        created_by=created_by,
        reversal_of=reversal_of,
        balance_after=new_balance,
    )

    balance.quantity_on_hand = new_balance
    balance.save(update_fields=["quantity_on_hand", "last_updated_at"])

    logger.info(
        "Inventory %s item=%s qty=%s balance=%s ref=%s:%s%s",
        transaction_type, item.code, quantity, new_balance, reference_type, reference_id,
        f" reverses={reversal_of.pk}" if reversal_of else "",
    )
    return tx


@transaction.atomic
def reverse_reference(*, reference_type: str, reference_id, user, reason: str, transaction_date=None) -> list:
    """
    Post opposite-direction entries for every not-yet-reversed transaction of a
    source document (production entry, delivery, adjustment). Idempotent: a
    second call finds nothing left to reverse and posts nothing.
    """
    originals = list(
        InventoryTransaction.objects.select_related("item")
        .filter(reference_type=reference_type, reference_id=reference_id, reversal_of__isnull=True)
        .exclude(reversed_by__isnull=False)
    )
    if not originals:
        return []

    lock_balances([tx.item for tx in originals])
    posting_date = transaction_date or timezone.localdate()

    # All-or-nothing: if any reversal would drive stock negative (e.g. the
    # delivered cassava was already consumed), the whole reversal rolls back.
    reversals = []
    for original in originals:
        reversals.append(
            record_inventory_transaction(
                item=original.item,
                transaction_type=_OPPOSITE[original.transaction_type],
                quantity=original.quantity,
                reference_type=original.reference_type,
                reference_id=original.reference_id,
                transaction_date=posting_date,
                created_by=user,
                notes=f"Reversal: {reason}",
                reversal_of=original,
            )
        )
    return reversals


@transaction.atomic
def post_manual_adjustment(*, item: InventoryItem, direction: str, quantity: Decimal, reason: str, user, transaction_date=None) -> InventoryTransaction:
    """Stock-count correction. Direction is IN (found stock) or OUT (loss / write-off)."""
    if direction not in (InventoryTransactionType.IN, InventoryTransactionType.OUT):
        raise BusinessLogicError("Adjustment direction must be IN or OUT.")
    if not reason or not reason.strip():
        raise BusinessLogicError("A reason is required for manual adjustments.")
    return record_inventory_transaction(
        item=item,
        transaction_type=direction,
        quantity=quantity,
        reference_type=InventoryReferenceType.MANUAL_ADJUSTMENT,
        reference_id=uuid.uuid4(),
        transaction_date=transaction_date or timezone.localdate(),
        created_by=user,
        notes=reason.strip(),
    )
