import csv
from io import BytesIO, StringIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from apps.production.models import ProductionEntry


def build_csv_report(queryset):
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Cassava Inflow (tons)", "Starch Output (tons)", "Yield (%)", "Downtime (minutes)"])

    for row in queryset:
        writer.writerow([
            row.production_date,
            row.cassava_inflow_tons,
            row.starch_output_tons,
            row.yield_percent,
            row.downtime_minutes,
        ])

    return buffer.getvalue()


def build_pdf_report(queryset, title="Production Report"):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, title)
    y -= 30

    p.setFont("Helvetica", 10)
    for row in queryset:
        line = (
            f"{row.production_date} | Inflow: {row.cassava_inflow_tons} tons | "
            f"Output: {row.starch_output_tons} tons | Yield: {row.yield_percent}% | "
            f"Downtime: {row.downtime_minutes} mins"
        )
        p.drawString(50, y, line[:110])
        y -= 18

        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = height - 50

    p.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes