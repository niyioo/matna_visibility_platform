import csv
from io import BytesIO, StringIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .selectors import active_entries
from .services import summarize

COLUMNS = ["Date", "Cassava Inflow (t)", "Starch Output (t)", "Yield (%)", "Downtime (min)"]


def _rows(start_date, end_date):
    return (
        active_entries(start_date, end_date)
        .order_by("production_date")
        .values_list("production_date", "cassava_inflow_tons", "starch_output_tons", "yield_percent", "downtime_minutes")
    )


def _fmt(value, places=2):
    return "—" if value is None else f"{value:,.{places}f}"


def build_csv_report(start_date, end_date) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    for date, inflow, output, yld, downtime in _rows(start_date, end_date):
        writer.writerow([date.isoformat(), inflow, output, yld, downtime])

    summary = summarize(start_date, end_date)
    writer.writerow([])
    writer.writerow(["Totals", summary["total_inflow"], summary["total_output"], summary["yield_percent"] or "", summary["total_downtime"]])
    writer.writerow(["Period", f"{start_date.isoformat()} to {end_date.isoformat()}"])
    writer.writerow(["Generated", timezone.localtime().strftime("%Y-%m-%d %H:%M %Z")])
    # BOM so Excel opens the UTF-8 file with the right encoding.
    return "﻿" + buffer.getvalue()


def build_pdf_report(start_date, end_date, title="Production Report") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, title=title,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    summary = summarize(start_date, end_date)
    story = [
        Paragraph(title, styles["Title"]),
        Paragraph(
            f"{start_date:%d %b %Y} – {end_date:%d %b %Y} · generated {timezone.localtime():%d %b %Y %H:%M}",
            styles["Normal"],
        ),
        Spacer(1, 8 * mm),
    ]

    summary_table = Table(
        [
            ["Total inflow", "Total output", "Yield", "Total downtime", "Entries"],
            [
                f"{_fmt(summary['total_inflow'])} t",
                f"{_fmt(summary['total_output'])} t",
                f"{_fmt(summary['yield_percent'])}%" if summary["yield_percent"] is not None else "—",
                f"{summary['total_downtime']:,} min",
                str(summary["entries_count"]),
            ],
        ],
        hAlign="LEFT",
    )
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748b")),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 12),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ]))
    story += [summary_table, Spacer(1, 6 * mm)]

    data = [COLUMNS] + [
        [f"{date:%d %b %Y}", _fmt(inflow), _fmt(output), _fmt(yld), f"{downtime:,}"]
        for date, inflow, output, yld, downtime in _rows(start_date, end_date)
    ]
    if len(data) == 1:
        story.append(Paragraph("No production entries in this period.", styles["Italic"]))
    else:
        table = Table(data, repeatRows=1, hAlign="LEFT", colWidths=[32 * mm, 34 * mm, 34 * mm, 26 * mm, 30 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(table)

    doc.build(story)
    return buffer.getvalue()
