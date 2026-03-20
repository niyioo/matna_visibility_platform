from django.core.management.base import BaseCommand
from apps.inventory.services import ensure_default_inventory_items


class Command(BaseCommand):
    help = "Seed default inventory items"

    def handle(self, *args, **options):
        ensure_default_inventory_items()
        self.stdout.write(self.style.SUCCESS("Default inventory items seeded successfully."))