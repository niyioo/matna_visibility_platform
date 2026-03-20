from datetime import date, timedelta, datetime

from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAnyOperationalRole
from apps.production.models import ProductionEntry
from .services import get_dashboard_snapshot, get_period_summary
from .selectors import get_yield_trend, get_inflow_vs_output_trend, get_downtime_trend
from .reports import build_csv_report, build_pdf_report


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


class DashboardView(APIView):
    permission_classes = [IsAnyOperationalRole]

    def get(self, request):
        return Response(get_dashboard_snapshot())


class PeriodSummaryView(APIView):
    permission_classes = [IsAnyOperationalRole]

    def get(self, request):
        period = request.query_params.get("period", "daily")
        start_date = parse_date(request.query_params.get("start_date"))
        end_date = parse_date(request.query_params.get("end_date"))
        return Response(get_period_summary(period, start_date=start_date, end_date=end_date))


class YieldTrendView(APIView):
    permission_classes = [IsAnyOperationalRole]

    def get(self, request):
        start_date = parse_date(request.query_params.get("start_date"))
        end_date = parse_date(request.query_params.get("end_date"))
        return Response(get_yield_trend(start_date=start_date, end_date=end_date))


class InflowVsOutputTrendView(APIView):
    permission_classes = [IsAnyOperationalRole]

    def get(self, request):
        start_date = parse_date(request.query_params.get("start_date"))
        end_date = parse_date(request.query_params.get("end_date"))
        return Response(get_inflow_vs_output_trend(start_date=start_date, end_date=end_date))


class DowntimeTrendView(APIView):
    permission_classes = [IsAnyOperationalRole]

    def get(self, request):
        start_date = parse_date(request.query_params.get("start_date"))
        end_date = parse_date(request.query_params.get("end_date"))
        return Response(get_downtime_trend(start_date=start_date, end_date=end_date))


class ExportCSVReportView(APIView):
    permission_classes = [IsAnyOperationalRole]

    def get(self, request):
        period = request.query_params.get("period", "daily")
        today = date.today()

        if period == "weekly":
            start_date = today - timedelta(days=6)
        elif period == "monthly":
            start_date = today.replace(day=1)
        else:
            start_date = today

        queryset = ProductionEntry.objects.filter(
            production_date__gte=start_date,
            production_date__lte=today,
        ).order_by("production_date")

        csv_data = build_csv_report(queryset)

        response = HttpResponse(csv_data, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="production_{period}_report.csv"'
        return response


class ExportPDFReportView(APIView):
    permission_classes = [IsAnyOperationalRole]

    def get(self, request):
        period = request.query_params.get("period", "daily")
        today = date.today()

        if period == "weekly":
            start_date = today - timedelta(days=6)
        elif period == "monthly":
            start_date = today.replace(day=1)
        else:
            start_date = today

        queryset = ProductionEntry.objects.filter(
            production_date__gte=start_date,
            production_date__lte=today,
        ).order_by("production_date")

        pdf_data = build_pdf_report(queryset, title=f"Production {period.title()} Report")

        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="production_{period}_report.pdf"'
        return response