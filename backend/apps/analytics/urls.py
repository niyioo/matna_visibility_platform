from django.urls import path

from .views import (
    DashboardView,
    DowntimeTrendView,
    ExportCSVReportView,
    ExportPDFReportView,
    InflowVsOutputTrendView,
    PeriodSummaryView,
    PlatformConfigView,
    TrendsView,
    YieldTrendView,
)

urlpatterns = [
    path("config/", PlatformConfigView.as_view(), name="analytics-config"),
    path("dashboard/", DashboardView.as_view(), name="analytics-dashboard"),
    path("summary/", PeriodSummaryView.as_view(), name="analytics-summary"),
    path("trends/", TrendsView.as_view(), name="analytics-trends"),
    path("yield-trend/", YieldTrendView.as_view(), name="analytics-yield-trend"),
    path("inflow-vs-output/", InflowVsOutputTrendView.as_view(), name="analytics-inflow-vs-output"),
    path("downtime-trend/", DowntimeTrendView.as_view(), name="analytics-downtime-trend"),
    path("reports/export/csv/", ExportCSVReportView.as_view(), name="analytics-report-export-csv"),
    path("reports/export/pdf/", ExportPDFReportView.as_view(), name="analytics-report-export-pdf"),
]
