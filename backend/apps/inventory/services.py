from decimal import Decimal
from django.db import transaction
from common.exceptions import BusinessLogicError
from common.constants import RAW_CASSAVA_CODE, FINISHED_STARCH_CODE
from .models import (
    InventoryItem,
    InventoryBalance,
    InventoryTransaction,
    InventoryTransactionType,
    InventoryReferenceType,
)


def get_or_create_inventory_item(code: str, name: str, item_type: str, unit: str = "tons") -> InventoryItem:
    item, _ = InventoryItem.objects.get_or_create(
        code=code,
        defaults={"name": name, "item_type": item_type, "unit": unit}
    )
    InventoryBalance.objects.get_or_create(item=item, defaults={"quantity_on_hand": Decimal("0.00")})
    return item


def ensure_default_inventory_items() -> None:
    from .models import InventoryItemType

    get_or_create_inventory_item(
        code=RAW_CASSAVA_CODE,
        name="Raw Cassava",
        item_type=InventoryItemType.RAW_MATERIAL,
    )
    get_or_create_inventory_item(
        code=FINISHED_STARCH_CODE,
        name="Finished Starch",
        item_type=InventoryItemType.FINISHED_GOOD,
    )


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
    notes: str = ""
) -> InventoryTransaction:
    balance, _ = InventoryBalance.objects.select_for_update().get_or_create(
        item=item,
        defaults={"quantity_on_hand": Decimal("0.00")}
    )

    if transaction_type == InventoryTransactionType.IN:
        new_balance = balance.quantity_on_hand + quantity
    elif transaction_type == InventoryTransactionType.OUT:
        new_balance = balance.quantity_on_hand - quantity
        if new_balance < 0:
            raise BusinessLogicError(f"Insufficient stock for item '{item.name}'.")
    elif transaction_type == InventoryTransactionType.ADJUSTMENT:
        new_balance = balance.quantity_on_hand + quantity
        if new_balance < 0:
            raise BusinessLogicError(f"Adjustment would make stock negative for item '{item.name}'.")
    else:
        raise BusinessLogicError("Invalid inventory transaction type.")

    transaction_record = InventoryTransaction.objects.create(
        item=item,
        transaction_type=transaction_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        transaction_date=transaction_date,
        notes=notes,
        created_by=created_by,
    )

    balance.quantity_on_hand = new_balance
    balance.save(update_fields=["quantity_on_hand", "last_updated_at"])

    return transaction_record


def get_raw_cassava_item() -> InventoryItem:
    ensure_default_inventory_items()
    return InventoryItem.objects.get(code=RAW_CASSAVA_CODE)


def get_finished_starch_item() -> InventoryItem:
    ensure_default_inventory_items()
    return InventoryItem.objects.get(code=FINISHED_STARCH_CODE)