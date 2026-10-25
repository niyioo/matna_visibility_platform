import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.inventory.reconciliation import (
    reconcile_inventory,
    rebuild_balances_from_ledger,
    repair_missing_postings,
)


class Command(BaseCommand):
    help = (
        "Check that inventory balances, the ledger and source documents agree. "
        "Exits with status 1 when discrepancies are found (suitable for cron alerting). "
        "Read-only unless --repair-missing or --rebuild-balances is given."
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Print the full report as JSON.")
        parser.add_argument(
            "--repair-missing", metavar="USERNAME",
            help="Post ledger entries for documents that have none, attributed to USERNAME (an admin).",
        )
        parser.add_argument(
            "--rebuild-balances", action="store_true",
            help="Reset cached balances to the ledger totals (run after the ledger is verified).",
        )

    def handle(self, *args, **options):
        if options["repair_missing"]:
            User = get_user_model()
            try:
                user = User.objects.get(username=options["repair_missing"], role="ADMIN", is_active=True)
            except User.DoesNotExist as exc:
                raise CommandError(f"No active admin named '{options['repair_missing']}'.") from exc
            result = repair_missing_postings(user=user)
            for line in result["repaired"]:
                self.stdout.write(self.style.SUCCESS(f"Repaired: {line}"))
            for failure in result["failed"]:
                self.stdout.write(self.style.ERROR(f"Failed: {failure['document']} — {failure['error']}"))

        if options["rebuild_balances"]:
            for change in rebuild_balances_from_ledger() or ["Balances already match the ledger."]:
                self.stdout.write(self.style.WARNING(change))

        report = reconcile_inventory()
        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2))
        else:
            for item in report["items"]:
                status = "OK " if item["in_sync"] else "BAD"
                self.stdout.write(f"[{status}] {item['item_code']}: balance {item['balance']} / ledger {item['ledger_total']}")
            for issue in report["issues"]:
                label = issue.get("document") or issue.get("item_code") or issue.get("reference_id")
                self.stdout.write(self.style.ERROR(f"- {issue['type']}: {label} {issue.get('differences') or issue.get('detail', '')}"))

        if report["is_consistent"]:
            self.stdout.write(self.style.SUCCESS("Inventory is consistent."))
        else:
            self.stderr.write(self.style.ERROR(f"{report['issue_count']} inventory discrepancies found."))
            raise SystemExit(1)
