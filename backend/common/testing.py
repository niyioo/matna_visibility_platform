"""Shared fixtures for the test suite."""
import itertools
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.inventory.services import ensure_default_inventory_items
from apps.suppliers.models import Supplier
from apps.suppliers.services import create_supplier_delivery

PASSWORD = "Str0ng-Pass!word"
_counter = itertools.count(1)


def days_ago(n: int):
    return timezone.localdate() - timedelta(days=n)


def make_user(role=UserRole.OPERATIONS, username=None, **extra):
    n = next(_counter)
    username = username or f"{role.lower()}_{n}"
    return User.objects.create_user(
        username=username, email=f"{username}@example.com", password=PASSWORD,
        role=role, is_staff=role == UserRole.ADMIN, **extra,
    )


class APITestBase(TestCase):
    """Creates one user per role, default inventory items and an unauthenticated client."""

    def setUp(self):
        cache.clear()  # throttle counters live in the cache
        ensure_default_inventory_items()
        self.admin = make_user(UserRole.ADMIN)
        self.ops = make_user(UserRole.OPERATIONS)
        self.mgmt = make_user(UserRole.MANAGEMENT)
        self.client = APIClient()
        self.supplier = Supplier.objects.create(name=f"Supplier {next(_counter)}")

    def login_as(self, user):
        self.client.force_authenticate(user=user)
        return self.client

    def seed_raw_stock(self, tons, on=None):
        return create_supplier_delivery(
            user=self.ops, supplier=self.supplier,
            delivery_date=on or days_ago(30), quantity_tons=Decimal(str(tons)),
        )
