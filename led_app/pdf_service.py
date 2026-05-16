"""Generate PDF temperature report with ReportLab."""
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)


def generate_pdf(readings) -> BytesIO:
    buf  = BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4,
                              rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=2*cm,   bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    story.append(Paragraph('Raport Temperatury', styles['Title']))
    story.append(Paragraph(
        f'Wygenerowano: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        styles['Normal']))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.5*cm))

    if readings:
        temps = [r.temperature for r in readings]
        story.append(Paragraph(
            f'Liczba pomiarów: <b>{len(temps)}</b> &nbsp;|&nbsp; '
            f'Min: <b>{min(temps):.1f} °C</b> &nbsp;|&nbsp; '
            f'Max: <b>{max(temps):.1f} °C</b> &nbsp;|&nbsp; '
            f'Średnia: <b>{sum(temps)/len(temps):.1f} °C</b>',
            styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        rows = [['Data i godzina', 'Temperatura (°C)', 'Wilgotność (%)']]
        for r in readings:
            rows.append([
                r.timestamp.strftime('%Y-%m-%d %H:%M'),
                f'{r.temperature:.2f}',
                f'{r.humidity:.1f}' if r.humidity is not None else '—',
            ])

        tbl = Table(rows, colWidths=[7*cm, 5*cm, 5*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1, 0), colors.HexColor('#111318')),
            ('TEXTCOLOR',      (0, 0), (-1, 0), colors.white),
            ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#f5f5f5'), colors.white]),
            ('GRID',           (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
            ('ALIGN',          (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',     (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl)
    else:
        story.append(Paragraph('Brak danych do wyświetlenia.', styles['Normal']))

    doc.build(story)
    buf.seek(0)
    return buf
