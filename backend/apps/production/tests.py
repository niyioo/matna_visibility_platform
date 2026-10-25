from decimal import Decimal

from django.db import IntegrityError, transaction
from rest_framework import status

from apps.inventory.models import InventoryBalance, InventoryTransaction
from common.constants import FINISHED_STARCH_CODE, RAW_CASSAVA_CODE
from common.testing import APITestBase, days_ago

from .models import ProductionEntry

URL = "/api/production/entries/"


def stock(code):
    return InventoryBalance.objects.get(item__code=code).quantity_on_hand


class ProductionEntryTests(APITestBase):
    def setUp(self):
        super().setUp()
        self.seed_raw_stock(1000)

    def payload(self, **overrides):
        data = {
            "production_date": days_ago(1).isoformat(),
            "cassava_inflow_tons": "100.00",
            "starch_output_tons": "28.00",
            "downtime_minutes": 15,
        }
        data.update(overrides)
        return data

    def create(self, user=None, **overrides):
        self.login_as(user or self.ops)
        return self.client.post(URL, self.payload(**overrides), format="json")

    # ── Happy path & ledger ──────────────────────────────────────────────────
    def test_create_posts_stock_movements_atomically(self):
        response = self.create()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["yield_percent"], "28.00")

        txs = InventoryTransaction.objects.filter(reference_id=response.data["id"])
        self.assertEqual(
            {(t.item.code, t.transaction_type, t.quantity) for t in txs},
            {(RAW_CASSAVA_CODE, "OUT", Decimal("100.00")), (FINISHED_STARCH_CODE, "IN", Decimal("28.00"))},
        )
        self.assertEqual(stock(RAW_CASSAVA_CODE), Decimal("900.00"))
        self.assertEqual(stock(FINISHED_STARCH_CODE), Decimal("28.00"))
        self.assertEqual(txs.get(item__code=RAW_CASSAVA_CODE).balance_after, Decimal("900.00"))

    def test_zero_output_day_posts_only_consumption(self):
        response = self.create(starch_output_tons="0")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InventoryTransaction.objects.filter(reference_id=response.data["id"]).count(), 1)

    def test_insufficient_raw_stock_rolls_back_everything(self):
        response = self.create(cassava_inflow_tons="5000.00", starch_output_tons="1000.00")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "insufficient_stock")
        self.assertFalse(ProductionEntry.objects.exists())
        self.assertEqual(stock(FINISHED_STARCH_CODE), Decimal("0.00"))

    # ── Validation ───────────────────────────────────────────────────────────
    def test_duplicate_active_date_rejected(self):
        self.create()
        response = self.create()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Void it first", response.data["errors"]["production_date"][0])
        self.assertEqual(ProductionEntry.objects.count(), 1)

    def test_output_exceeding_inflow_reports_field_error(self):
        response = self.create(cassava_inflow_tons="50", starch_output_tons="60")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("starch_output_tons", response.data["errors"])
        self.assertIn("exceed", response.data["detail"])

    def test_rejects_future_date_zero_inflow_and_impossible_downtime(self):
        cases = [
            {"production_date": days_ago(-1).isoformat()},
            {"cassava_inflow_tons": "0", "starch_output_tons": "0"},
            {"downtime_minutes": 1441},
            {"downtime_minutes": -5},
            {"cassava_inflow_tons": "abc"},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                self.assertEqual(self.create(**overrides).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(ProductionEntry.objects.exists())

    def test_database_rejects_impossible_yield_even_without_api(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductionEntry.objects.create(
                production_date=days_ago(3), cassava_inflow_tons=Decimal("10"),
                starch_output_tons=Decimal("11"), created_by=self.ops,
            )

    # ── Permissions ──────────────────────────────────────────────────────────
    def test_role_permissions(self):
        self.assertEqual(self.create(user=self.mgmt).status_code, status.HTTP_403_FORBIDDEN)
        self.login_as(self.mgmt)
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_200_OK)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_entries_are_immutable_via_api(self):
        entry_id = self.create().data["id"]
        for method in ("put", "patch", "delete"):
            with self.subTest(method=method):
                self.login_as(self.admin)
                response = getattr(self.client, method)(f"{URL}{entry_id}/", {"notes": "x"}, format="json")
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # ── Void / correction ────────────────────────────────────────────────────
    def void(self, entry_id, user=None, reason="Wrong scale reading"):
        self.login_as(user or self.admin)
        return self.client.post(f"{URL}{entry_id}/void/", {"reason": reason}, format="json")

    def test_void_reverses_stock_and_allows_corrected_reentry(self):
        entry_id = self.create().data["id"]
        response = self.void(entry_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_voided"])
        self.assertEqual(stock(RAW_CASSAVA_CODE), Decimal("1000.00"))
        self.assertEqual(stock(FINISHED_STARCH_CODE), Decimal("0.00"))

        corrected = self.create(cassava_inflow_tons="90.00", starch_output_tons="27.00")
        self.assertEqual(corrected.status_code, status.HTTP_201_CREATED)
        self.login_as(self.ops)
        listed = self.client.get(URL).data["results"]
        self.assertEqual([e["id"] for e in listed], [corrected.data["id"]])
        audit = self.client.get(f"{URL}?is_voided=true").data["results"]
        self.assertEqual([e["id"] for e in audit], [entry_id])

    def test_void_is_admin_only_requires_reason_and_happens_once(self):
        entry_id = self.create().data["id"]
        self.assertEqual(self.void(entry_id, user=self.ops).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.void(entry_id, reason="").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.void(entry_id).status_code, status.HTTP_200_OK)
        second = self.void(entry_id)
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(second.data["code"], "already_voided")
        self.assertEqual(stock(RAW_CASSAVA_CODE), Decimal("1000.00"))

    def test_void_blocked_when_produced_starch_already_gone(self):
        entry_id = self.create().data["id"]
        self.login_as(self.admin)
        self.client.post("/api/inventory/adjustments/", {
            "item_code": FINISHED_STARCH_CODE, "direction": "OUT", "quantity": "20.00", "reason": "Dispatched to customer",
        }, format="json")
        response = self.void(entry_id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "insufficient_stock")
        self.assertFalse(ProductionEntry.objects.get(pk=entry_id).is_voided)
        self.assertEqual(stock(RAW_CASSAVA_CODE), Decimal("900.00"))
