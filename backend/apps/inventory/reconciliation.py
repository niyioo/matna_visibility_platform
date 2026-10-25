"""
Inventory reconciliation.

Three independent sources must agree:
  1. InventoryBalance.quantity_on_hand       (cached running total)
  2. Sum of InventoryTransaction rows         (the append-only ledger)
  3. Source documents — production entries and supplier deliveries

`reconcile_inventory()` reports every disagreement. It never changes data.
`repair_missing_postings()` and `rebuild_balances_from_ledger()` are explicit,
opt-in fixes used by the `reconcile_inventory` management command.
"""
import logging
from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.db.models import Case, DecimalField, F, Sum, When

from apps.production.models import ProductionEntry
from apps.suppliers.models import SupplierDelivery
from common.constants import FINISHED_STARCH_CODE, RAW_CASSAVA_CODE

from .models import (
    InventoryBalance,
    InventoryReferenceType,
    InventoryTransaction,
    InventoryTransactionType,
)
from common.utils import quantize_two_places

from .services import get_finished_starch_item, get_raw_cassava_item, record_inventory_transaction

logger = logging.getLogger(__name__)

ZERO = Decimal("0.00")

SIGNED_QUANTITY = Case(
    When(transaction_type=InventoryTransactionType.OUT, then=-F("quantity")),
    default=F("quantity"),
    output_field=DecimalField(max_digits=14, decimal_places=2),
)


def _ledger_by_reference():
    """{(reference_type, reference_id_str): {item_code: net_quantity}} plus row counts."""
    rows = (
        InventoryTransaction.objects.values("reference_type", "reference_id", "item__code")
        .annotate(net=Sum(SIGNED_QUANTITY))
    )
    net = defaultdict(dict)
    for row in rows:
        net[(row["reference_type"], str(row["reference_id"]))][row["item__code"]] = quantize_two_places(row["net"] or ZERO)
    return net


def _expected_for_entry(entry):
    if entry.is_voided:
        return {RAW_CASSAVA_CODE: ZERO, FINISHED_STARCH_CODE: ZERO}
    return {RAW_CASSAVA_CODE: -entry.cassava_inflow_tons, FINISHED_STARCH_CODE: entry.starch_output_tons}


def _expected_for_delivery(delivery):
    return {RAW_CASSAVA_CODE: ZERO if delivery.is_voided else delivery.quantity_tons}


def _compare(expected: dict, actual: dict):
    diffs = {}
    for code in set(expected) | set(actual):
        exp = expected.get(code, ZERO)
        act = actual.get(code, ZERO)
        if exp != act:
            diffs[code] = {"expected": str(exp), "ledger": str(act), "difference": str(act - exp)}
    return diffs


def reconcile_inventory() -> dict:
    issues = []

    # 1. Cached balance vs ledger total, per item.
    ledger_totals = {
        row["item_id"]: quantize_two_places(row["total"] or ZERO)
        for row in InventoryTransaction.objects.values("item_id").annotate(total=Sum(SIGNED_QUANTITY))
    }
    items = []
    for balance in InventoryBalance.objects.select_related("item"):
        ledger_total = ledger_totals.get(balance.item_id, ZERO)
        ok = ledger_total == balance.quantity_on_hand
        items.append({
            "item_code": balance.item.code,
            "item_name": balance.item.name,
            "balance": str(balance.quantity_on_hand),
            "ledger_total": str(ledger_total),
            "in_sync": ok,
        })
        if not ok:
            issues.append({
                "type": "balance_drift",
                "item_code": balance.item.code,
                "detail": f"Cached balance {balance.quantity_on_hand} ≠ ledger total {ledger_total}.",
            })

    # 2. Source documents vs their ledger postings.
    ledger = _ledger_by_reference()
    seen_refs = set()

    for entry in ProductionEntry.objects.all().iterator():
        key = (InventoryReferenceType.PRODUCTION_ENTRY, str(entry.id))
        seen_refs.add(key)
        diffs = _compare(_expected_for_entry(entry), ledger.get(key, {}))
        if diffs:
            issues.append({
                "type": "missing_posting" if key not in ledger else "posting_mismatch",
                "reference_type": key[0],
                "reference_id": key[1],
                "document": f"Production entry {entry.production_date}{' (voided)' if entry.is_voided else ''}",
                "differences": diffs,
            })

    for delivery in SupplierDelivery.objects.select_related("supplier").iterator():
        key = (InventoryReferenceType.SUPPLIER_DELIVERY, str(delivery.id))
        seen_refs.add(key)
        diffs = _compare(_expected_for_delivery(delivery), ledger.get(key, {}))
        if diffs:
            issues.append({
                "type": "missing_posting" if key not in ledger else "posting_mismatch",
                "reference_type": key[0],
                "reference_id": key[1],
                "document": f"Delivery from {delivery.supplier.name} on {delivery.delivery_date}"
                            f"{' (voided)' if delivery.is_voided else ''}",
                "differences": diffs,
            })

    # 3. Ledger rows pointing at documents that don't exist.
    document_types = {InventoryReferenceType.PRODUCTION_ENTRY, InventoryReferenceType.SUPPLIER_DELIVERY}
    for key in ledger:
        if key[0] in document_types and key not in seen_refs:
            issues.append({
                "type": "orphan_posting",
                "reference_type": key[0],
                "reference_id": key[1],
                "detail": "Ledger postings reference a document that does not exist.",
            })

    return {"is_consistent": not issues, "issue_count": len(issues), "items": items, "issues": issues}


def repair_missing_postings(*, user) -> dict:
    """
    Posts ledger entries for live documents that have NO postings at all
    (e.g. rows created through the admin before it was locked down).
    Partial mismatches are reported, never auto-corrected.
    """
    ledger_refs = set(
        (rt, str(rid))
        for rt, rid in InventoryTransaction.objects.values_list("reference_type", "reference_id").distinct()
    )
    raw, starch = get_raw_cassava_item(), get_finished_starch_item()
    repaired, failed = [], []

    # Deliveries first (chronologically) so production OUT postings have stock to draw on.
    deliveries = SupplierDelivery.objects.active().select_related("supplier").order_by("delivery_date", "created_at")
    for delivery in deliveries:
        if (InventoryReferenceType.SUPPLIER_DELIVERY, str(delivery.id)) in ledger_refs:
            continue
        try:
            record_inventory_transaction(
                item=raw,
                transaction_type=InventoryTransactionType.IN,
                quantity=delivery.quantity_tons,
                reference_type=InventoryReferenceType.SUPPLIER_DELIVERY,
                reference_id=delivery.id,
                transaction_date=delivery.delivery_date,
                created_by=user,
                notes=f"Reconciliation: missing posting for delivery from {delivery.supplier.name}",
            )
            repaired.append(f"Delivery {delivery.id} ({delivery.delivery_date}, {delivery.quantity_tons} t)")
        except Exception as exc:  # noqa: BLE001 — report and continue with the next document
            failed.append({"document": f"Delivery {delivery.id}", "error": str(exc)})

    for entry in ProductionEntry.objects.active().order_by("production_date", "created_at"):
        if (InventoryReferenceType.PRODUCTION_ENTRY, str(entry.id)) in ledger_refs:
            continue
        try:
            with transaction.atomic():
                record_inventory_transaction(
                    item=raw,
                    transaction_type=InventoryTransactionType.OUT,
                    quantity=entry.cassava_inflow_tons,
                    reference_type=InventoryReferenceType.PRODUCTION_ENTRY,
                    reference_id=entry.id,
                    transaction_date=entry.production_date,
                    created_by=user,
                    notes="Reconciliation: missing posting (cassava consumed)",
                )
                if entry.starch_output_tons > 0:
                    record_inventory_transaction(
                        item=starch,
                        transaction_type=InventoryTransactionType.IN,
                        quantity=entry.starch_output_tons,
                        reference_type=InventoryReferenceType.PRODUCTION_ENTRY,
                        reference_id=entry.id,
                        transaction_date=entry.production_date,
                        created_by=user,
                        notes="Reconciliation: missing posting (starch produced)",
                    )
            repaired.append(f"Production entry {entry.id} ({entry.production_date})")
        except Exception as exc:  # noqa: BLE001
            failed.append({"document": f"Production entry {entry.id}", "error": str(exc)})

    logger.warning("Reconciliation repair by %s: %d repaired, %d failed", user.username, len(repaired), len(failed))
    return {"repaired": repaired, "failed": failed}


@transaction.atomic
def rebuild_balances_from_ledger() -> list:
    """Resets each cached balance to its ledger total. Use only after the ledger is verified."""
    changes = []
    totals = {
        row["item_id"]: quantize_two_places(row["total"] or ZERO)
        for row in InventoryTransaction.objects.values("item_id").annotate(total=Sum(SIGNED_QUANTITY))
    }
    for balance in InventoryBalance.objects.select_for_update().select_related("item"):
        target = totals.get(balance.item_id, ZERO)
        if balance.quantity_on_hand != target:
            changes.append(f"{balance.item.code}: {balance.quantity_on_hand} → {target}")
            balance.quantity_on_hand = target
            balance.save(update_fields=["quantity_on_hand", "last_updated_at"])
    return changes
