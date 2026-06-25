from datetime import datetime
# rename it to reporter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)


def generate_report(report):

    filename = "trust_report.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "SachAI Trust Report",
            styles["Title"]
        )
    )

    content.append(
        Spacer(1, 20)
    )

    content.append(
        Paragraph(
            f"<b>Claim:</b> {report['claim']}",
            styles["BodyText"]
        )
    )

    content.append(
        Spacer(1, 10)
    )

    content.append(
        Paragraph(
            f"<b>Processed Claim:</b> {report['processed_claim']}",
            styles["BodyText"]
        )
    )

    content.append(
        Spacer(1, 10)
    )
    content.append(
    Paragraph(
        f"<b>AI Label:</b> {report['ai_label']}",
        styles["BodyText"]
    )
)

    content.append(
    Paragraph(
        f"<b>AI Score:</b> {report['ai_label']}%",
        styles["BodyText"]
    )
    )
    content.append(
        Paragraph(
            f"<b>AI Score:</b> {report['ai_score']}%",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Fact Verdict:</b> {report['fact_verdict']}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Fact Score:</b> {report['fact_score']}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Source:</b> {report['source_name']}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Source Score:</b> {report['source_score']}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Final Trust Score:</b> {report['trust_score']}",
            styles["BodyText"]
        )
    )
    content.append(
    Paragraph(
        f"<b>Generated At:</b> {datetime.now()}",
        styles["BodyText"]
    )
   )
    content.append(
    Paragraph(
        "<b>Status:</b> Demo Report",
        styles["BodyText"]
    )
    )
    doc.build(content)

    return filename