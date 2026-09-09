from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

from metadata import DEVELOPER_NAME, RESEARCH_PAPER_TITLE, INSTITUTION, SHORT_NAME
from recommendations import allocation_guidance

NAVY = colors.HexColor("#18324A")
TEAL = colors.HexColor("#147D73")
TEAL_DARK = colors.HexColor("#0F5E56")
TEAL_MID = colors.HexColor("#59A99E")
TEAL_LIGHT = colors.HexColor("#EAF6F3")
GREEN_SOFT = colors.HexColor("#F4FAF8")
GREY = colors.HexColor("#667085")
BORDER = colors.HexColor("#D0D5DD")
WHITE = colors.white

def _footer(canvas, doc):
    canvas.saveState()
    page_w, _ = A4
    canvas.setStrokeColor(BORDER)
    canvas.line(doc.leftMargin, 13.5*mm, page_w - doc.rightMargin, 13.5*mm)
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 6.4)
    canvas.drawCentredString(
        page_w / 2.0, 10.4*mm,
        f"Developed by {DEVELOPER_NAME} | {INSTITUTION} | {SHORT_NAME} research-derived decision-support tool"
    )
    canvas.setFont("Helvetica-Oblique", 6.0)
    canvas.drawCentredString(
        page_w / 2.0, 7.7*mm,
        f'Research paper: "{RESEARCH_PAPER_TITLE}"'
    )
    canvas.restoreState()

def build_pdf(assessment, result, plan, benchmarks, evidence_lines, assessment_ref, model_version):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16*mm,
        leftMargin=16*mm,
        topMargin=14*mm,
        bottomMargin=21*mm,
        title="HMAF Management Allocation Assessment",
        author=DEVELOPER_NAME,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="HMAFTitle", parent=styles["Title"], fontSize=18, leading=21,
        textColor=TEAL_DARK, alignment=TA_CENTER, spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name="HMAFSub", parent=styles["Heading2"], fontSize=11.5, leading=14,
        textColor=NAVY, alignment=TA_CENTER, spaceAfter=9
    ))
    styles.add(ParagraphStyle(
        name="H2x", parent=styles["Heading2"], fontSize=12.5, leading=15,
        textColor=TEAL_DARK, spaceBefore=8, spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name="BodySmall", parent=styles["BodyText"], fontSize=8.7, leading=11.5,
        textColor=NAVY, spaceAfter=3.5
    ))
    styles.add(ParagraphStyle(
        name="BodyBox", parent=styles["BodyText"], fontSize=9, leading=12,
        textColor=NAVY, spaceAfter=0
    ))
    styles.add(ParagraphStyle(
        name="SmallGrey", parent=styles["BodyText"], fontSize=7.2, leading=9,
        textColor=GREY
    ))

    story = [
        Paragraph("Hybrid Management Allocation Framework", styles["HMAFTitle"]),
        Paragraph("HMAF Management Allocation Assessment", styles["HMAFSub"]),
    ]

    meta = [
        ["Assessment reference", assessment_ref],
        ["Model version", f"HMAF {model_version}"],
        ["Assessment name", assessment.get("assessment_name") or "Not specified"],
        ["Assessment level", assessment["scope"]],
        ["Project stage", assessment["project_stage"]],
        ["Project value", assessment["project_value"]],
        ["Concurrent projects", assessment["concurrent_projects"]],
        ["Management activity", assessment["activity"]],
    ]
    t = Table(meta, colWidths=[47*mm, 121*mm])
    t.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.35, BORDER),
        ("BACKGROUND", (0,0), (0,-1), TEAL_LIGHT),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,0), (-1,-1), NAVY),
        ("FONTSIZE", (0,0), (-1,-1), 8.2),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t)

    story.append(Paragraph("Management allocation result", styles["H2x"]))
    result_table = Table([
        ["Digital Suitability", "Physical Presence Need", "HMOS", "Allocation guidance"],
        [f"{result.digital_suitability:.2f}/5", f"{result.physical_presence_need:.2f}/5",
         f"{result.hmos:.2f}/5", result.orientation]
    ], colWidths=[38*mm, 42*mm, 28*mm, 60*mm])
    result_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), TEAL_DARK),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), TEAL_LIGHT),
        ("TEXTCOLOR", (0,1), (-1,-1), NAVY),
        ("ALIGN", (0,0), (2,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.35, BORDER),
        ("FONTSIZE", (0,0), (-1,-1), 8.2),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(result_table)

    story.append(Spacer(1, 3*mm))
    guidance_table = Table(
        [[Paragraph(
            f"<b>{result.orientation.upper()}</b><br/>{allocation_guidance(result.orientation_code)}",
            styles["BodyBox"]
        )]],
        colWidths=[168*mm]
    )
    guidance_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), GREEN_SOFT),
        ("BOX", (0,0), (-1,-1), 0.8, TEAL),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(guidance_table)

    story.append(Paragraph("Management Allocation Plan", styles["H2x"]))
    for heading, key in [
        ("Manage digitally", "digital"),
        ("Retain onsite", "onsite"),
        ("Improve / strengthen", "improve"),
        ("Reassess when", "reassess"),
    ]:
        group = [Paragraph(f"<b>{heading}</b>", styles["BodySmall"])]
        for item in plan.get(key, []):
            if item and str(item).strip().lower() != "null":
                group.append(Paragraph(f"• {item}", styles["BodySmall"]))
        story.append(KeepTogether(group))

    if benchmarks:
        story.append(Paragraph("Research benchmarks relevant to this assessment", styles["H2x"]))
        rows = [["Study situation", "Mean /5", "Hybrid"]]
        for b in benchmarks:
            rows.append([b["label"], f'{b["mean"]:.2f}', f'{b["hybrid"]:.1f}%'])
        bt = Table(rows, colWidths=[96*mm, 32*mm, 40*mm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), TEAL),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BACKGROUND", (0,1), (-1,-1), GREEN_SOFT),
            ("TEXTCOLOR", (0,1), (-1,-1), NAVY),
            ("GRID", (0,0), (-1,-1), 0.35, BORDER),
            ("FONTSIZE", (0,0), (-1,-1), 8.2),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(bt)

    if evidence_lines:
        story.append(Paragraph("Evidence informing this assessment", styles["H2x"]))
        for line in evidence_lines:
            story.append(Paragraph(f"• {line}", styles["BodySmall"]))

    story.append(Paragraph("Important limitations", styles["H2x"]))
    story.append(Paragraph(
        "The HMAF/HMOS is a research-derived decision-support model, not a validated predictive equation. "
        "It does not replace WHS duties, statutory obligations, contractual requirements, mandatory inspections, "
        "competent supervision or professional judgement. Equal weighting is retained at this prototype stage because "
        "the study does not estimate validated coefficients for all six HMAF factors. HMOS must not be interpreted as a fixed onsite-attendance percentage.",
        styles["BodySmall"]
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(f"{assessment_ref} • HMAF Version {model_version}", styles["SmallGrey"]))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer.getvalue()
