from django.conf import settings
from datetime import timedelta
from decimal import Decimal

from django.test import override_settings
from django.utils import timezone
from rest_framework import status

from apps.production.services import create_production_entry, void_production_entry
from common.testing import APITestBase, days_ago


class AnalyticsTests(APITestBase):
    def setUp(self):
        super().setUp()
        self.seed_raw_stock(10_000, on=days_ago(60))
        self.login_as(self.mgmt)

    def entry(self, days, inflow, output, downtime=0):
        return create_production_entry(
            user=self.ops, production_date=days_ago(days), cassava_inflow_tons=Decimal(str(inflow)),
            starch_output_tons=Decimal(str(output)), downtime_minutes=downtime,
        )

    def get(self, path, **params):
        return self.client.get(f"/api/analytics/{path}/", params)

    # ── KPI accuracy ─────────────────────────────────────────────────────────
    def test_yield_is_tonnage_weighted_not_average_of_days(self):
        self.entry(1, 100, 10)   # 10%
        self.entry(2, 10, 5)     # 50%
        data = self.get("summary", period="weekly").data
        # (10 + 5) / (100 + 10) = 13.64%, whereas averaging days would claim 30%.
        self.assertAlmostEqual(data["yield_percent"], 13.64, places=2)
        self.assertEqual(data["total_inflow"], 110.0)
        self.assertEqual(data["entries_count"], 2)

    def test_voided_entries_excluded_everywhere(self):
        kept = self.entry(1, 100, 30)
        voided = self.entry(2, 100, 5)
        void_production_entry(entry_id=voided.id, user=self.admin, reason="Bad reading")
        self.assertEqual(self.get("summary", period="weekly").data["entries_count"], 1)
        series = self.get("trends").data["series"]
        self.assertEqual([row["production_date"] for row in series], [kept.production_date])
        self.assertEqual(self.get("dashboard").data["latest_yield"], 30.0)

    def test_summary_compares_with_previous_equal_window(self):
        self.entry(1, 100, 30, downtime=10)
        self.entry(9, 100, 20, downtime=60)
        cmp = self.get("summary", period="weekly").data["comparison"]
        self.assertEqual(cmp["yield_percent"]["trend"], "up")
        self.assertTrue(cmp["yield_percent"]["favourable"])
        self.assertEqual(cmp["total_downtime"]["trend"], "down")
        self.assertTrue(cmp["total_downtime"]["favourable"])

    def test_empty_period_is_well_formed(self):
        data = self.get("summary", period="daily").data
        self.assertEqual(data["entries_count"], 0)
        self.assertIsNone(data["yield_percent"])

    # ── Input validation ─────────────────────────────────────────────────────
    def test_rejects_bad_ranges_and_periods(self):
        today = timezone.localdate()
        bad = [
            ("summary", {"period": "yearly"}),
            ("trends", {"start_date": "not-a-date"}),
            ("trends", {"start_date": today.isoformat(), "end_date": (today - timedelta(days=1)).isoformat()}),
            ("trends", {"start_date": (today - timedelta(days=400)).isoformat(), "end_date": today.isoformat()}),
            ("reports/export/csv", {"period": 'daily"\r\nX-Injected: 1'}),
        ]
        for path, params in bad:
            with self.subTest(path=path, params=params):
                response = self.get(path, **params)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_trends_default_to_bounded_window(self):
        self.entry(5, 100, 30)
        self.entry(45, 100, 30)
        data = self.get("trends").data
        self.assertEqual(len(data["series"]), 1)
        self.assertEqual((data["end_date"] - data["start_date"]).days, 29)

    # ── Alerts & anomalies ───────────────────────────────────────────────────
    def test_dashboard_alerts_and_health(self):
        for day in range(10, 3, -1):
            self.entry(day, 100, 29)
        self.entry(3, 100, 15, downtime=200)  # low yield + severe downtime + statistical outlier
        data = self.get("dashboard").data
        codes = {a["code"] for a in data["alerts"]}
        self.assertTrue({"LOW_YIELD", "HIGH_DOWNTIME", "YIELD_ANOMALY", "STALE_DATA"} <= codes, codes)
        self.assertEqual(data["health"], "critical")
        self.assertEqual(data["alerts"][0]["severity"], "critical")
        flagged = [row for row in self.get("trends").data["series"] if row["yield_anomaly"]]
        self.assertEqual([row["production_date"] for row in flagged], [days_ago(3)])

    @override_settings(OPERATIONS_THRESHOLDS={
        "YIELD_TARGET_PERCENT": 28, "YIELD_CRITICAL_PERCENT": 22, "YIELD_MAX_PLAUSIBLE_PERCENT": 40, "DOWNTIME_WARNING_MINUTES": 60,
        "DOWNTIME_CRITICAL_MINUTES": 180, "STOCK_COVER_WARNING_DAYS": 500, "STOCK_COVER_CRITICAL_DAYS": 1,
        "STALE_DATA_DAYS": 2, "ANOMALY_SIGMA": 2.0,
    })
    def test_low_stock_cover_alert(self):
        self.entry(0, 100, 30)
        data = self.get("dashboard").data
        self.assertIn("RAW_STOCK_LOW", {a["code"] for a in data["alerts"]})
        self.assertAlmostEqual(data["raw_stock_cover_days"], 99.0)

    def test_implausible_yield_flagged_as_data_quality_issue(self):
        self.entry(0, 50, 30)  # 60% — not achievable for cassava starch
        codes = {a["code"] for a in self.get("dashboard").data["alerts"]}
        self.assertIn("IMPLAUSIBLE_YIELD", codes)
        self.assertNotIn("BELOW_TARGET_YIELD", codes)

    @override_settings(PLATFORM_SETTINGS={**settings.PLATFORM_SETTINGS, "MAX_RANGE_DAYS": 10})
    def test_limits_follow_settings_and_are_published(self):
        config = self.get("config").data
        self.assertEqual(config["limits"]["max_range_days"], 10)
        self.assertEqual(config["thresholds"]["yield_target_percent"], 28)
        self.assertEqual([p["value"] for p in config["periods"]], ["daily", "weekly", "monthly"])
        response = self.get("trends", start_date=days_ago(12).isoformat(), end_date=days_ago(0).isoformat())
        self.assertEqual(response.status_code, 400)
        self.assertIn("10 days", response.data["detail"])

    def test_dashboard_includes_trends(self):
        self.entry(1, 100, 28)
        data = self.get("dashboard").data
        self.assertEqual(len(data["trends"]["series"]), 1)

    def test_empty_dashboard(self):
        data = self.get("dashboard").data
        self.assertIsNone(data["snapshot_date"])
        self.assertEqual(data["alerts"][0]["code"], "NO_DATA")

    # ── Reports ──────────────────────────────────────────────────────────────
    def test_csv_export(self):
        self.entry(1, 100, 28)
        response = self.get("reports/export/csv", period="weekly")
        self.assertEqual(response.status_code, 200)
        self.assertIn('filename="matna_production_', response["Content-Disposition"])
        body = response.content.decode("utf-8-sig")
        self.assertIn("Cassava Inflow (t)", body)
        self.assertIn("Totals,100.0,28.0,28.0,0", body)

    def test_pdf_export(self):
        self.entry(1, 100, 28)
        response = self.get("reports/export/pdf", start_date=days_ago(7).isoformat(), end_date=days_ago(0).isoformat())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_requires_known_role(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.get("dashboard").status_code, status.HTTP_401_UNAUTHORIZED)
