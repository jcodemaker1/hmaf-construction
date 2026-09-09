from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak
)

from metadata import DEVELOPER_NAME, RESEARCH_PAPER_TITLE, INSTITUTION, SHORT_NAME
from recommendations import allocation_guidance
from evidence import RESEARCH_FACTS

NAVY = colors.HexColor("#18324A")
TEAL = colors.HexColor("#147D73")
TEAL_DARK = colors.HexColor("#0F5E56")
TEAL_MID = colors.HexColor("#59A99E")
TEAL_LIGHT = colors.HexColor("#EAF6F3")
GREEN_SOFT = colors.HexColor("#F4FAF8")
GREEN_MID = colors.HexColor("#D7EEE8")
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

def _benchmark_position(delta):
    if abs(delta) < 0.05:
        return "Broadly aligned with study benchmark"
    if delta > 0:
        return f"{abs(delta):.2f} points more digitally oriented"
    return f"{abs(delta):.2f} points more physically oriented"

def _governance_status(ai_used, human_review, accountability, validation):
    if not ai_used:
        return "Not triggered", "AI / automated monitoring was not selected for this assessment."
    if human_review and accountability and validation:
        return "Satisfied", "Human review, clear decision accountability and source/output validation are all recorded."
    missing = []
    if not human_review:
        missing.append("human review")
    if not accountability:
        missing.append("clear decision accountability")
    if not validation:
        missing.append("source/output validation")
    return "Action required", "Missing safeguard(s): " + ", ".join(missing) + "."

def build_pdf(
    assessment,
    result,
    plan,
    benchmarks,
    evidence_lines,
    assessment_ref,
    model_version,
    inputs,
    ai_used,
    human_review,
    accountability,
    validation,
    sensitivity,
):
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
        name="PageTitle", parent=styles["Heading1"], fontSize=15.5, leading=19,
        textColor=TEAL_DARK, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="H2x", parent=styles["Heading2"], fontSize=12.2, leading=14.5,
        textColor=TEAL_DARK, spaceBefore=7, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="H3x", parent=styles["Heading3"], fontSize=9.6, leading=12,
        textColor=NAVY, spaceBefore=4, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name="BodySmall", parent=styles["BodyText"], fontSize=8.5, leading=11.0,
        textColor=NAVY, spaceAfter=3.2
    ))
    styles.add(ParagraphStyle(
        name="BodyTiny", parent=styles["BodyText"], fontSize=7.8, leading=10,
        textColor=NAVY, spaceAfter=2.5
    ))
    styles.add(ParagraphStyle(
        name="BodyBox", parent=styles["BodyText"], fontSize=8.8, leading=11.5,
        textColor=NAVY, spaceAfter=0
    ))
    styles.add(ParagraphStyle(
        name="SmallGrey", parent=styles["BodyText"], fontSize=7.0, leading=9,
        textColor=GREY
    ))

    story = []

    # =======================================================
    # PAGE 1 - MANAGEMENT ALLOCATION ASSESSMENT
    # =======================================================
    story.append(Paragraph("Hybrid Management Allocation Framework", styles["HMAFTitle"]))
    story.append(Paragraph("HMAF Management Allocation Assessment", styles["HMAFSub"]))

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
        ("FONTSIZE", (0,0), (-1,-1), 8.0),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 3.7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3.7),
    ]))
    story.append(t)

    story.append(Paragraph("Management allocation result", styles["H2x"]))
    result_table = Table([
        ["Digital Suitability", "Physical Presence Need", "HMOS", "Allocation guidance"],
        [
            f"{result.digital_suitability:.2f}/5",
            f"{result.physical_presence_need:.2f}/5",
            f"{result.hmos:.2f}/5",
            result.orientation,
        ]
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
        ("FONTSIZE", (0,0), (-1,-1), 8.0),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(result_table)

    story.append(Spacer(1, 2.5*mm))
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
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(guidance_table)

    story.append(Paragraph("Management Allocation Plan", styles["H2x"]))
    for heading, key in [
        ("Manage digitally", "digital"),
        ("Retain onsite", "onsite"),
        ("Improve / strengthen", "improve"),
        ("Reassess when", "reassess"),
    ]:
        group = [Paragraph(f"<b>{heading}</b>", styles["BodyTiny"])]
        for item in plan.get(key, []):
            if item and str(item).strip().lower() != "null":
                group.append(Paragraph(f"• {item}", styles["BodyTiny"]))
        story.append(KeepTogether(group))

    if benchmarks:
        story.append(Paragraph("Research benchmarks relevant to this assessment", styles["H2x"]))
        rows = [["Study situation", "Mean /5", "Hybrid", "Relationship to your HMOS"]]
        for b in benchmarks:
            delta = result.hmos - b["mean"]
            rows.append([
                b["label"],
                f'{b["mean"]:.2f}',
                f'{b["hybrid"]:.1f}%',
                _benchmark_position(delta),
            ])
        bt = Table(rows, colWidths=[69*mm, 22*mm, 22*mm, 55*mm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), TEAL),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BACKGROUND", (0,1), (-1,-1), GREEN_SOFT),
            ("TEXTCOLOR", (0,1), (-1,-1), NAVY),
            ("GRID", (0,0), (-1,-1), 0.35, BORDER),
            ("FONTSIZE", (0,0), (-1,-1), 7.5),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("TOPPADDING", (0,0), (-1,-1), 3.4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3.4),
        ]))
        story.append(bt)

    # Intentional page break: no orphan heading.
    story.append(PageBreak())

    # =======================================================
    # PAGE 2 - EVIDENCE & DECISION RATIONALE
    # =======================================================
    story.append(Paragraph("Evidence & Decision Rationale", styles["PageTitle"]))
    story.append(Paragraph(
        "This page explains what drove the allocation, the reliability of the digital environment, "
        "the governance safeguards recorded and the conditions that could change the HMOS.",
        styles["BodySmall"]
    ))

    digital_drivers = sorted([
        ("Information suitability", float(inputs["I"])),
        ("Concurrency / scalability", float(inputs["C"])),
        ("Digital-system reliability", float(result.digital_reliability)),
    ], key=lambda x: x[1], reverse=True)

    presence_drivers = sorted([
        ("Risk / consequence", float(inputs["R"])),
        ("Verification / site context", float(inputs["V"])),
        ("Leadership / relational requirement", float(inputs["L"])),
    ], key=lambda x: x[1], reverse=True)

    story.append(Paragraph("Why this result was produced", styles["H2x"]))
    driver_rows = [
        ["Digital drivers", "Score", "Physical-presence drivers", "Score"],
    ]
    max_len = max(len(digital_drivers), len(presence_drivers))
    for i in range(max_len):
        d_name, d_score = digital_drivers[i] if i < len(digital_drivers) else ("", "")
        p_name, p_score = presence_drivers[i] if i < len(presence_drivers) else ("", "")
        driver_rows.append([
            d_name, f"{d_score:.2f}/5" if d_name else "",
            p_name, f"{p_score:.2f}/5" if p_name else "",
        ])
    driver_table = Table(driver_rows, colWidths=[58*mm, 25*mm, 60*mm, 25*mm])
    driver_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (1,0), TEAL_DARK),
        ("BACKGROUND", (2,0), (3,0), TEAL),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), GREEN_SOFT),
        ("GRID", (0,0), (-1,-1), 0.35, BORDER),
        ("FONTSIZE", (0,0), (-1,-1), 8.0),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ALIGN", (1,1), (1,-1), "CENTER"),
        ("ALIGN", (3,1), (3,-1), "CENTER"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(driver_table)
    story.append(Paragraph(
        f"<b>Strongest digital driver:</b> {digital_drivers[0][0]} ({digital_drivers[0][1]:.2f}/5). "
        f"<b>Strongest physical-presence driver:</b> {presence_drivers[0][0]} ({presence_drivers[0][1]:.2f}/5).",
        styles["BodySmall"]
    ))

    story.append(Paragraph("Digital Environment Reliability", styles["H2x"]))
    readiness_rows = [
        ["Overall D", "Devices", "Connectivity", "Information quality", "Integration"],
        [
            f"{result.digital_reliability:.2f}/5",
            f"{inputs['devices']}/5",
            f"{inputs['connectivity']}/5",
            f"{inputs['information_quality']}/5",
            f"{inputs['integration']}/5",
        ],
    ]
    readiness_table = Table(readiness_rows, colWidths=[30*mm, 31*mm, 34*mm, 39*mm, 34*mm])
    readiness_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), TEAL),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), TEAL_LIGHT),
        ("TEXTCOLOR", (0,1), (-1,-1), NAVY),
        ("GRID", (0,0), (-1,-1), 0.35, BORDER),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTSIZE", (0,0), (-1,-1), 7.8),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(readiness_table)

    if result.digital_reliability < 3:
        readiness_message = (
            "Digital readiness is below the neutral/adequate point. Strengthen the weakest readiness conditions "
            "before increasing digital reliance."
        )
    elif result.digital_reliability >= 4:
        readiness_message = "The selected digital environment is strong and can support greater digital reliance where task conditions permit."
    else:
        readiness_message = "The selected digital environment is adequate/mixed; continued monitoring of information quality, connectivity and integration is appropriate."
    story.append(Paragraph(readiness_message, styles["BodySmall"]))

    story.append(Paragraph("Governance & emerging technology", styles["H2x"]))
    gov_status, gov_message = _governance_status(
        ai_used, human_review, accountability, validation
    )
    gov_rows = [
        ["AI / automated monitoring", "Human review", "Decision accountability", "Data/output validation", "Status"],
        [
            "Yes" if ai_used else "No",
            ("Yes" if human_review else "No") if ai_used else "N/A",
            ("Yes" if accountability else "No") if ai_used else "N/A",
            ("Yes" if validation else "No") if ai_used else "N/A",
            gov_status,
        ],
    ]
    gov_table = Table(gov_rows, colWidths=[39*mm, 30*mm, 38*mm, 37*mm, 24*mm])
    gov_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), TEAL_DARK),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), GREEN_SOFT),
        ("TEXTCOLOR", (0,1), (-1,-1), NAVY),
        ("GRID", (0,0), (-1,-1), 0.35, BORDER),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTSIZE", (0,0), (-1,-1), 7.2),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(gov_table)
    story.append(Paragraph(gov_message, styles["BodySmall"]))

    story.append(Paragraph("Evidence informing this assessment", styles["H2x"]))
    if evidence_lines:
        for line in evidence_lines:
            story.append(Paragraph(f"• {line}", styles["BodyTiny"]))
    story.append(Paragraph(
        f"• Physical presence for safety-critical judgement had an RII of "
        f"{RESEARCH_FACTS['safety_rII']:.3f}, while digital information visibility and general hybrid effectiveness "
        f"each had an RII of {RESEARCH_FACTS['digital_visibility_rII']:.3f}.",
        styles["BodyTiny"]
    ))
    story.append(Paragraph(
        f"• Digital-system reliability was positively associated with perceived digital effectiveness "
        f"(r_s = {RESEARCH_FACTS['digital_reliability_effectiveness_rs']:.3f}) and remained independently associated "
        f"in the exploratory regression (B = {RESEARCH_FACTS['digital_reliability_regression_B']:.3f}, "
        f"p = {RESEARCH_FACTS['digital_reliability_regression_p']:.3f}).",
        styles["BodyTiny"]
    ))

    story.append(Paragraph("What could change the allocation?", styles["H2x"]))
    changed = [s for s in sensitivity if s.get("changed_category")]
    if changed:
        story.append(Paragraph(
            "The following one-point changes would move the assessment into another HMOS category if the underlying project conditions genuinely changed:",
            styles["BodyTiny"]
        ))
        selected_sensitivity = changed[:3]
    else:
        story.append(Paragraph(
            "No single one-point change tested would move this assessment into a different HMOS category. "
            "The most influential tested changes are shown below:",
            styles["BodyTiny"]
        ))
        selected_sensitivity = sensitivity[:3]

    for s in selected_sensitivity:
        prefix = "<b>Category change:</b> " if s.get("changed_category") else ""
        story.append(Paragraph(
            f"• {prefix}{s['label']}; HMOS would become {s['new_hmos']:.2f} ({s['new_orientation']}).",
            styles["BodyTiny"]
        ))
    story.append(Paragraph(
        "Sensitivity outputs are explanatory only and should not be used to manipulate scores. "
        "Inputs should change only when actual project conditions change.",
        styles["SmallGrey"]
    ))

    story.append(Paragraph("Important limitations", styles["H2x"]))
    story.append(Paragraph(
        "The HMAF/HMOS is a research-derived decision-support model, not a validated predictive equation. "
        "It does not replace WHS duties, statutory obligations, contractual requirements, mandatory inspections, "
        "competent supervision or professional judgement. Equal weighting is retained at this prototype stage because "
        "the study does not estimate validated coefficients for all six HMAF factors. HMOS must not be interpreted as "
        "a fixed onsite-attendance percentage.",
        styles["BodyTiny"]
    ))
    story.append(Spacer(1, 1.5*mm))
    story.append(Paragraph(f"{assessment_ref} • HMAF Version {model_version}", styles["SmallGrey"]))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer.getvalue()
