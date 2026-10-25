from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from common.dates import resolve_range, validate_period
from common.permissions import IsAnyOperationalRole

from .reports import build_csv_report, build_pdf_report
from .services import get_dashboard_snapshot, get_period_summary, get_platform_config, get_trends


class AnalyticsView(APIView):
    permission_classes = [IsAnyOperationalRole]


class PlatformConfigView(AnalyticsView):
    """Thresholds, analysis windows, input limits and refresh cadence for the UI."""

    def get(self, request):
        return Response(get_platform_config())


class DashboardView(AnalyticsView):
    def get(self, request):
        return Response(get_dashboard_snapshot())


class PeriodSummaryView(AnalyticsView):
    """?period=daily|weekly|monthly or ?start_date=&end_date= — includes the previous equal-length window."""

    def get(self, request):
        period = validate_period(request.query_params.get("period", "daily"))
        start, end = resolve_range(request.query_params, default_period=period)
        custom = bool(request.query_params.get("start_date") or request.query_params.get("end_date"))
        return Response(get_period_summary(start, end, period="custom" if custom else period))


class TrendsView(AnalyticsView):
    """All daily series in one request, with anomaly flags. Defaults to the last 30 days."""

    def get(self, request):
        start, end = resolve_range(request.query_params)
        return Response(get_trends(start, end))


class _SeriesView(AnalyticsView):
    """Legacy single-series endpoints, kept for API compatibility."""

    fields: tuple = ()

    def get(self, request):
        start, end = resolve_range(request.query_params)
        series = get_trends(start, end)["series"]
        return Response([{k: row[k] for k in ("production_date", *self.fields)} for row in series])


class YieldTrendView(_SeriesView):
    fields = ("yield_percent",)


class InflowVsOutputTrendView(_SeriesView):
    fields = ("cassava_inflow_tons", "starch_output_tons")


class DowntimeTrendView(_SeriesView):
    fields = ("downtime_minutes",)


class _ExportView(AnalyticsView):
    content_type = ""
    extension = ""

    def build(self, start, end, title):
        raise NotImplementedError

    def get(self, request):
        period = validate_period(request.query_params.get("period", "daily"))
        start, end = resolve_range(request.query_params, default_period=period)
        title = f"Matna Production Report — {start:%d %b %Y} to {end:%d %b %Y}"

        response = HttpResponse(self.build(start, end, title), content_type=self.content_type)
        # Filename is built only from validated values, never raw query input.
        response["Content-Disposition"] = (
            f'attachment; filename="matna_production_{start.isoformat()}_{end.isoformat()}.{self.extension}"'
        )
        response["Cache-Control"] = "no-store"
        return response


class ExportCSVReportView(_ExportView):
    content_type = "text/csv; charset=utf-8"
    extension = "csv"

    def build(self, start, end, title):
        return build_csv_report(start, end)


class ExportPDFReportView(_ExportView):
    content_type = "application/pdf"
    extension = "pdf"

    def build(self, start, end, title):
        return build_pdf_report(start, end, title=title)
