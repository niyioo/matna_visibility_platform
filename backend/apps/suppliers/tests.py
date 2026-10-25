from decimal import Decimal

from rest_framework import status

from apps.inventory.models import InventoryBalance
from apps.production.services import create_production_entry
from common.constants import RAW_CASSAVA_CODE
from common.testing import APITestBase, days_ago

from .models import Supplier, SupplierDelivery

DELIVERIES = "/api/suppliers/deliveries/"


def raw_stock():
    return InventoryBalance.objects.get(item__code=RAW_CASSAVA_CODE).quantity_on_hand


class SupplierTests(APITestBase):
    def test_create_and_case_insensitive_duplicate(self):
        self.login_as(self.ops)
        self.assertEqual(self.client.post("/api/suppliers/", {"name": "Adeola Farms"}, format="json").status_code, 201)
        dup = self.client.post("/api/suppliers/", {"name": "adeola farms"}, format="json")
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already exists", dup.data["detail"])

    def test_update_keeping_own_name_succeeds(self):
        self.login_as(self.ops)
        response = self.client.put(
            f"/api/suppliers/{self.supplier.pk}/", {"name": self.supplier.name, "phone": "0800"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], "0800")

    def test_delete_deactivates_instead_of_breaking_history(self):
        self.seed_raw_stock(10)
        self.login_as(self.ops)
        self.assertEqual(self.client.delete(f"/api/suppliers/{self.supplier.pk}/").status_code, 204)
        self.assertFalse(Supplier.objects.get(pk=self.supplier.pk).is_active)
        self.assertEqual(SupplierDelivery.objects.count(), 1)

    def test_management_can_read_but_not_write(self):
        self.login_as(self.mgmt)
        self.assertEqual(self.client.get(f"/api/suppliers/{self.supplier.pk}/").status_code, 200)
        self.assertEqual(self.client.post("/api/suppliers/", {"name": "X"}, format="json").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/suppliers/{self.supplier.pk}/", {"name": "X"}, format="json").status_code, 403)

    def test_mass_assignment_of_read_only_fields_is_ignored(self):
        self.login_as(self.ops)
        response = self.client.post("/api/suppliers/", {
            "name": "Sneaky Ltd", "id": "00000000-0000-0000-0000-000000000001",
            "created_at": "2000-01-01T00:00:00Z", "is_active": False,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data["id"], "00000000-0000-0000-0000-000000000001")
        self.assertTrue(response.data["is_active"])


class DeliveryTests(APITestBase):
    def post(self, **overrides):
        self.login_as(self.ops)
        data = {"supplier": str(self.supplier.pk), "delivery_date": days_ago(1).isoformat(), "quantity_tons": "40.50"}
        data.update(overrides)
        return self.client.post(DELIVERIES, data, format="json")

    def test_delivery_increases_raw_stock(self):
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["supplier_name"], self.supplier.name)
        self.assertEqual(response.data["received_by_name"], self.ops.username)
        self.assertEqual(raw_stock(), Decimal("40.50"))

    def test_validation(self):
        inactive = Supplier.objects.create(name="Dormant", is_active=False)
        for overrides in ({"quantity_tons": "0"}, {"quantity_tons": "-3"},
                          {"delivery_date": days_ago(-2).isoformat()}, {"supplier": str(inactive.pk)}):
            with self.subTest(overrides=overrides):
                self.assertEqual(self.post(**overrides).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(raw_stock(), Decimal("0.00"))

    def test_received_by_cannot_be_spoofed(self):
        response = self.post(received_by=str(self.admin.pk))
        self.assertEqual(response.data["received_by"], self.ops.pk)

    def test_void_reverses_stock(self):
        delivery_id = self.post().data["id"]
        self.login_as(self.admin)
        response = self.client.post(f"{DELIVERIES}{delivery_id}/void/", {"reason": "Duplicate ticket"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(raw_stock(), Decimal("0.00"))
        self.login_as(self.ops)
        self.assertEqual(self.client.get(DELIVERIES).data["count"], 0)

    def test_void_refused_when_cassava_already_consumed(self):
        delivery_id = self.post(quantity_tons="100").data["id"]
        create_production_entry(
            user=self.ops, production_date=days_ago(0), cassava_inflow_tons=Decimal("80"),
            starch_output_tons=Decimal("20"), downtime_minutes=0,
        )
        self.login_as(self.admin)
        response = self.client.post(f"{DELIVERIES}{delivery_id}/void/", {"reason": "Duplicate ticket"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "insufficient_stock")
        self.assertFalse(SupplierDelivery.objects.get(pk=delivery_id).is_voided)
        self.assertEqual(raw_stock(), Decimal("20.00"))
