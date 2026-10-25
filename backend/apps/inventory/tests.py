import uuid
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError, transaction
from rest_framework import status

from apps.production.services import create_production_entry
from apps.suppliers.models import SupplierDelivery
from common.constants import FINISHED_STARCH_CODE, RAW_CASSAVA_CODE
from common.testing import APITestBase, days_ago

from .models import ImmutableRecordError, InventoryBalance, InventoryReferenceType, InventoryTransaction
from .reconciliation import reconcile_inventory, rebuild_balances_from_ledger, repair_missing_postings
from .services import get_raw_cassava_item, lock_balances, record_inventory_transaction, reverse_reference


def balance(code):
    return InventoryBalance.objects.get(item__code=code).quantity_on_hand


class LedgerTests(APITestBase):
    def test_transactions_are_immutable(self):
        delivery = self.seed_raw_stock(100)
        tx = InventoryTransaction.objects.get(reference_id=delivery.id)
        tx.quantity = Decimal("1")
        with self.assertRaises(ImmutableRecordError):
            tx.save()
        with self.assertRaises(ImmutableRecordError):
            tx.delete()

    def test_non_positive_quantity_rejected(self):
        for qty in (Decimal("0"), Decimal("-5")):
            with self.subTest(qty=qty), self.assertRaises(Exception):
                record_inventory_transaction(
                    item=get_raw_cassava_item(), transaction_type="IN", quantity=qty,
                    reference_type=InventoryReferenceType.MANUAL_ADJUSTMENT, reference_id=uuid.uuid4(),
                    transaction_date=days_ago(0), created_by=self.admin,
                )

    def test_database_forbids_negative_balance(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            InventoryBalance.objects.filter(item__code=RAW_CASSAVA_CODE).update(quantity_on_hand=Decimal("-1"))

    def test_reversal_is_idempotent_and_single_use(self):
        delivery = self.seed_raw_stock(100)
        args = dict(reference_type=InventoryReferenceType.SUPPLIER_DELIVERY, reference_id=delivery.id, user=self.admin, reason="test")
        self.assertEqual(len(reverse_reference(**args)), 1)
        self.assertEqual(reverse_reference(**args), [])
        self.assertEqual(balance(RAW_CASSAVA_CODE), Decimal("0.00"))

        original = InventoryTransaction.objects.get(reference_id=delivery.id, reversal_of__isnull=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            InventoryTransaction.objects.create(
                item=original.item, transaction_type="OUT", quantity=original.quantity,
                reference_type=original.reference_type, reference_id=original.reference_id,
                transaction_date=days_ago(0), created_by=self.admin, reversal_of=original,
            )

    def test_lock_balances_uses_deterministic_order(self):
        with transaction.atomic():
            locked = lock_balances([get_raw_cassava_item(), InventoryBalance.objects.get(item__code=FINISHED_STARCH_CODE).item])
        self.assertEqual(len(locked), 2)


class AdjustmentAPITests(APITestBase):
    URL = "/api/inventory/adjustments/"

    def post(self, user, **data):
        self.login_as(user)
        body = {"item_code": RAW_CASSAVA_CODE, "direction": "IN", "quantity": "10.00", "reason": "Stock count found extra"}
        body.update(data)
        return self.client.post(self.URL, body, format="json")

    def test_admin_only(self):
        self.assertEqual(self.post(self.ops).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.post(self.mgmt).status_code, status.HTTP_403_FORBIDDEN)
        response = self.post(self.admin)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["reference_type"], "MANUAL_ADJUSTMENT")
        self.assertEqual(balance(RAW_CASSAVA_CODE), Decimal("10.00"))

    def test_validation(self):
        self.assertEqual(self.post(self.admin, reason="").status_code, 400)
        self.assertEqual(self.post(self.admin, quantity="0").status_code, 400)
        self.assertEqual(self.post(self.admin, direction="ADJUSTMENT").status_code, 400)
        self.assertEqual(self.post(self.admin, item_code="NOPE").status_code, 400)
        write_off = self.post(self.admin, direction="OUT", quantity="999")
        self.assertEqual(write_off.data["code"], "insufficient_stock")

    def test_inventory_endpoints_are_read_only_for_everyone(self):
        self.login_as(self.admin)
        for url in ("/api/inventory/balances/", "/api/inventory/transactions/"):
            self.assertEqual(self.client.post(url, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ReconciliationTests(APITestBase):
    def test_consistent_after_normal_operations(self):
        self.seed_raw_stock(500)
        create_production_entry(
            user=self.ops, production_date=days_ago(2), cassava_inflow_tons=Decimal("100"),
            starch_output_tons=Decimal("30"), downtime_minutes=0,
        )
        report = reconcile_inventory()
        self.assertTrue(report["is_consistent"], report["issues"])

    def test_detects_and_repairs_document_without_postings(self):
        # Simulates a delivery created outside the service layer (e.g. old admin edits).
        SupplierDelivery.objects.create(
            supplier=self.supplier, delivery_date=days_ago(5), quantity_tons=Decimal("300"), received_by=self.ops,
        )
        report = reconcile_inventory()
        self.assertFalse(report["is_consistent"])
        self.assertEqual(report["issues"][0]["type"], "missing_posting")

        result = repair_missing_postings(user=self.admin)
        self.assertEqual(len(result["repaired"]), 1)
        self.assertEqual(balance(RAW_CASSAVA_CODE), Decimal("300.00"))
        self.assertTrue(reconcile_inventory()["is_consistent"])

    def test_detects_balance_drift_and_rebuilds(self):
        self.seed_raw_stock(200)
        InventoryBalance.objects.filter(item__code=RAW_CASSAVA_CODE).update(quantity_on_hand=Decimal("150"))
        issues = reconcile_inventory()["issues"]
        self.assertEqual([i["type"] for i in issues], ["balance_drift"])
        self.assertEqual(rebuild_balances_from_ledger(), [f"{RAW_CASSAVA_CODE}: 150.00 → 200.00"])
        self.assertTrue(reconcile_inventory()["is_consistent"])

    def test_management_command_exit_status(self):
        call_command("reconcile_inventory", stdout=StringIO())  # consistent: no exception
        InventoryBalance.objects.filter(item__code=RAW_CASSAVA_CODE).update(quantity_on_hand=Decimal("7"))
        with self.assertRaises(SystemExit) as ctx:
            call_command("reconcile_inventory", stdout=StringIO(), stderr=StringIO())
        self.assertEqual(ctx.exception.code, 1)

    def test_endpoint_admin_only(self):
        self.login_as(self.mgmt)
        self.assertEqual(self.client.get("/api/inventory/reconciliation/").status_code, 403)
        self.login_as(self.admin)
        self.assertTrue(self.client.get("/api/inventory/reconciliation/").data["is_consistent"])
