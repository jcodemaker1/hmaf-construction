from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak

from metadata import DEVELOPER_NAME, RESEARCH_PAPER_TITLE, INSTITUTION, SHORT_NAME
from recommendations import allocation_guidance
from evidence import TASK_PRESENCE_EVIDENCE

NAVY = colors.HexColor("#18324A")
TEAL = colors.HexColor("#147D73")
TEAL_DARK = colors.HexColor("#0F5E56")
TEAL_LIGHT = colors.HexColor("#EAF6F3")
GREEN_SOFT = colors.HexColor("#F4FAF8")
BLUE_SOFT = colors.HexColor("#EAF3FF")
AMBER_SOFT = colors.HexColor("#FFF7DE")
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
    canvas.drawCentredString(page_w/2, 10.4*mm, f"Developed by {DEVELOPER_NAME} | {INSTITUTION} | {SHORT_NAME} research-derived decision-support tool")
    canvas.setFont("Helvetica-Oblique", 6.0)
    canvas.drawCentredString(page_w/2, 7.7*mm, f'Research paper: "{RESEARCH_PAPER_TITLE}"')
    canvas.restoreState()


def _governance_status(ai_used, human_review, accountability, validation):
    if not ai_used:
        return "Not triggered", "AI / automated monitoring was not selected for this assessment."
    if human_review and accountability and validation:
        return "Controls recorded", "Human review, clear decision accountability and source/output validation were confirmed by the assessor."
    missing = []
    if not human_review: missing.append("human review")
    if not accountability: missing.append("clear decision accountability")
    if not validation: missing.append("source/output validation")
    return "Action required", "Missing safeguard(s): " + ", ".join(missing) + "."


def build_pdf(assessment, result, plan, context_anchors, research_messages, assessment_ref, model_version, inputs, ai_used, human_review, accountability, validation, sensitivity):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=14*mm, bottomMargin=21*mm, title="HMAF Management Allocation Assessment", author=DEVELOPER_NAME)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="HMAFTitle", parent=styles["Title"], fontSize=18, leading=21, textColor=TEAL_DARK, alignment=TA_CENTER, spaceAfter=5))
    styles.add(ParagraphStyle(name="HMAFSub", parent=styles["Heading2"], fontSize=11.5, leading=14, textColor=NAVY, alignment=TA_CENTER, spaceAfter=9))
    styles.add(ParagraphStyle(name="PageTitle", parent=styles["Heading1"], fontSize=15.5, leading=19, textColor=TEAL_DARK, spaceAfter=8))
    styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontSize=12.0, leading=14.2, textColor=TEAL_DARK, spaceBefore=6, spaceAfter=3.5))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=8.25, leading=10.5, textColor=NAVY, spaceAfter=2.8))
    styles.add(ParagraphStyle(name="BodyTiny", parent=styles["BodyText"], fontSize=7.5, leading=9.2, textColor=NAVY, spaceAfter=2.0))
    styles.add(ParagraphStyle(name="BodyBox", parent=styles["BodyText"], fontSize=8.6, leading=11, textColor=NAVY, spaceAfter=0))
    styles.add(ParagraphStyle(name="SmallGrey", parent=styles["BodyText"], fontSize=6.9, leading=8.6, textColor=GREY))

    story = [Paragraph("Hybrid Management Allocation Framework", styles["HMAFTitle"]), Paragraph("HMAF Management Allocation Assessment", styles["HMAFSub"])]

    meta = [
        ["Assessment reference", assessment_ref], ["Model version", f"HMAF {model_version}"], ["Assessment name", assessment.get("assessment_name") or "Not specified"],
        ["Assessment level", assessment["scope"]], ["Project stage", assessment["project_stage"]], ["High-risk / critical stage", "Yes" if assessment["high_risk_critical_stage"] else "No"],
        ["Project value", assessment["project_value"]], ["Concurrent projects", assessment["concurrent_projects"]], ["Management activity", assessment["activity"]],
    ]
    t = Table(meta, colWidths=[47*mm,121*mm])
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.35,BORDER),("BACKGROUND",(0,0),(0,-1),TEAL_LIGHT),("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("TEXTCOLOR",(0,0),(-1,-1),NAVY),("FONTSIZE",(0,0),(-1,-1),7.8),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),3.2),("BOTTOMPADDING",(0,0),(-1,-1),3.2)]))
    story.append(t)

    story.append(Paragraph("Management allocation result", styles["H2x"]))
    rt = Table([["Digital Suitability","Physical Presence Need","Base HMOS","Final HMOS"],[f"{result.digital_suitability:.2f}/5",f"{result.physical_presence_need:.2f}/5",f"{result.base_hmos:.2f}/5",f"{result.hmos:.2f}/5"]], colWidths=[42*mm,46*mm,38*mm,42*mm])
    rt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),TEAL_DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,-1),TEAL_LIGHT),("TEXTCOLOR",(0,1),(-1,-1),NAVY),("ALIGN",(0,0),(-1,-1),"CENTER"),("GRID",(0,0),(-1,-1),0.35,BORDER),("FONTSIZE",(0,0),(-1,-1),7.9),("TOPPADDING",(0,0),(-1,-1),4.5),("BOTTOMPADDING",(0,0),(-1,-1),4.5)]))
    story.append(rt)

    story.append(Spacer(1,2*mm))
    gt = Table([[Paragraph(f"<b>{result.orientation.upper()}</b><br/>{allocation_guidance(result.orientation_code)}", styles["BodyBox"]) ]], colWidths=[168*mm])
    gt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GREEN_SOFT),("BOX",(0,0),(-1,-1),0.8,TEAL),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story.append(gt)

    pct = TASK_PRESENCE_EVIDENCE.get(assessment["activity"])
    if pct is not None and pct >= 90:
        st = Table([[Paragraph(f"<b>OPERATIONAL PHYSICAL-PRESENCE SAFEGUARD</b><br/>{pct:.1f}% of study respondents identified this activity as requiring physical presence. Physical presence should be retained for the assessed activity regardless of the wider hybrid allocation.", styles["BodyBox"]) ]], colWidths=[168*mm])
        st.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),AMBER_SOFT),("BOX",(0,0),(-1,-1),0.7,colors.HexColor("#C78300")),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),4.5),("BOTTOMPADDING",(0,0),(-1,-1),4.5)]))
        story.extend([Spacer(1,1.5*mm),st])

    story.append(Paragraph("How project context influenced the HMOS", styles["H2x"]))
    cr = [["Factor-based HMOS","Context anchor","After context calibration","Task safeguard","Final HMOS"],[f"{result.base_hmos:.2f}",f"{result.context_anchor:.2f}" if result.context_anchor is not None else "None",f"{result.context_calibrated_hmos:.2f}",f"Cap {result.task_cap:.2f}" if result.task_cap is not None else "None",f"{result.hmos:.2f}"]]
    ct = Table(cr,colWidths=[32*mm,34*mm,42*mm,31*mm,29*mm])
    ct.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),TEAL),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,-1),BLUE_SOFT),("GRID",(0,0),(-1,-1),0.35,BORDER),("ALIGN",(0,0),(-1,-1),"CENTER"),("FONTSIZE",(0,0),(-1,-1),7.0),("TOPPADDING",(0,0),(-1,-1),3.6),("BOTTOMPADDING",(0,0),(-1,-1),3.6)]))
    story.append(ct)
    story.append(Paragraph("Where directly matched survey situations exist, HMAF calibrates the factor-based score toward the mean orientation reported in those situations. The factor-based score retains twice the influence of the context anchor. Task-specific physical-presence safeguards are applied separately.", styles["SmallGrey"]))

    story.append(Paragraph("Management Allocation Plan", styles["H2x"]))
    for heading,key in [("Manage digitally","digital"),("Retain onsite","onsite"),("Improve / strengthen","improve"),("Reassess when","reassess")]:
        group=[Paragraph(f"<b>{heading}</b>",styles["BodyTiny"])]
        for item in plan.get(key,[]): group.append(Paragraph(f"• {item}",styles["BodyTiny"]))
        story.append(KeepTogether(group))

    story.append(PageBreak())
    story.append(Paragraph("Research Evidence & Decision Rationale", styles["PageTitle"]))
    story.append(Paragraph("The following evidence explains why the selected project context and management activity influenced the assessment. Study findings are practitioner-grounded and are not population-wide predictive coefficients.", styles["BodySmall"]))

    story.append(Paragraph("Research evidence applied to this assessment", styles["H2x"]))
    for msg in research_messages: story.append(Paragraph(f"• {msg}", styles["BodyTiny"]))

    if context_anchors:
        story.append(Paragraph("Context calibration inputs", styles["H2x"]))
        rows=[["Matched study situation","Observed mean /5","Hybrid category"]]
        for a in context_anchors: rows.append([a["label"],f"{a['mean']:.2f}",f"{a['hybrid']:.1f}%"])
        at=Table(rows,colWidths=[98*mm,34*mm,36*mm])
        at.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),TEAL_DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,-1),GREEN_SOFT),("GRID",(0,0),(-1,-1),0.35,BORDER),("FONTSIZE",(0,0),(-1,-1),7.6)]))
        story.append(at)

    digital_drivers=sorted([("Information suitability",float(inputs["I"])),("Concurrent project load (C)",float(inputs["C"])),("Digital-system reliability",float(result.digital_reliability))],key=lambda x:x[1],reverse=True)
    presence_drivers=sorted([("Risk / consequence",float(inputs["R"])),("Verification / site context",float(inputs["V"])),("Leadership / relational requirement",float(inputs["L"]))],key=lambda x:x[1],reverse=True)
    story.append(Paragraph("Why this result was produced", styles["H2x"]))
    rows=[["Digital drivers","Score","Physical-presence drivers","Score"]]+[[digital_drivers[i][0],f"{digital_drivers[i][1]:.2f}/5",presence_drivers[i][0],f"{presence_drivers[i][1]:.2f}/5"] for i in range(3)]
    dt=Table(rows,colWidths=[58*mm,25*mm,60*mm,25*mm])
    dt.setStyle(TableStyle([("BACKGROUND",(0,0),(1,0),TEAL_DARK),("BACKGROUND",(2,0),(3,0),TEAL),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,-1),GREEN_SOFT),("GRID",(0,0),(-1,-1),0.35,BORDER),("FONTSIZE",(0,0),(-1,-1),7.6),("ALIGN",(1,1),(1,-1),"CENTER"),("ALIGN",(3,1),(3,-1),"CENTER")]))
    story.append(dt)

    story.append(Paragraph("Digital Environment Reliability", styles["H2x"]))
    rows=[["Overall D","Devices","Connectivity","Information quality","Integration"],[f"{result.digital_reliability:.2f}/5",f"{inputs['devices']}/5",f"{inputs['connectivity']}/5",f"{inputs['information_quality']}/5",f"{inputs['integration']}/5"]]
    et=Table(rows,colWidths=[30*mm,31*mm,34*mm,39*mm,34*mm])
    et.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),TEAL),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,-1),TEAL_LIGHT),("GRID",(0,0),(-1,-1),0.35,BORDER),("ALIGN",(0,0),(-1,-1),"CENTER"),("FONTSIZE",(0,0),(-1,-1),7.4)]))
    story.append(et)
    weak=[(n,s) for n,s in [("Devices",inputs["devices"]),("Connectivity",inputs["connectivity"]),("Information quality",inputs["information_quality"]),("Integration",inputs["integration"])] if s<3]
    if weak: story.append(Paragraph("<b>Attention required:</b> "+", ".join(f"{n} = {s}/5" for n,s in weak)+".", styles["BodySmall"]))

    story.append(Paragraph("Governance & emerging technology", styles["H2x"]))
    status,message=_governance_status(ai_used,human_review,accountability,validation)
    rows=[["AI / automated monitoring","Human review","Decision accountability","Data/output validation","Status"],["Yes" if ai_used else "No",("Yes" if human_review else "No") if ai_used else "N/A",("Yes" if accountability else "No") if ai_used else "N/A",("Yes" if validation else "No") if ai_used else "N/A",status]]
    gv=Table(rows,colWidths=[39*mm,30*mm,38*mm,37*mm,24*mm])
    gv.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),TEAL_DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("BACKGROUND",(0,1),(-1,-1),GREEN_SOFT),("GRID",(0,0),(-1,-1),0.35,BORDER),("ALIGN",(0,0),(-1,-1),"CENTER"),("FONTSIZE",(0,0),(-1,-1),6.9)]))
    story.extend([gv,Paragraph(message,styles["BodySmall"])])

    story.append(Paragraph("What could change the allocation?", styles["H2x"]))
    changed=[s for s in sensitivity if s.get("changed_category")]
    selected=changed[:3] if changed else sensitivity[:3]
    story.append(Paragraph("Selected one-point changes are shown below. They are explanatory only and should be changed only when actual project conditions change.",styles["BodyTiny"]))
    for s in selected:
        prefix="<b>Category change:</b> " if s.get("changed_category") else ""
        story.append(Paragraph(f"• {prefix}{s['label']}; HMOS would become {s['new_hmos']:.2f} ({s['new_orientation']}).", styles["BodyTiny"]))

    story.append(Paragraph("Important limitations", styles["H2x"]))
    story.append(Paragraph("HMAF is a research-derived decision-support model, not a validated predictive equation. The context calibration and task safeguards in Version 0.06 are transparent prototype decision rules derived from directly matched study findings; they are not regression coefficients and require future validation. HMAF does not replace WHS duties, statutory obligations, contractual requirements, mandatory inspections, competent supervision or professional judgement. HMOS must not be interpreted as a fixed onsite-attendance percentage.", styles["BodyTiny"]))
    story.append(Paragraph(f"{assessment_ref} • HMAF Version {model_version}", styles["SmallGrey"]))

    doc.build(story,onFirstPage=_footer,onLaterPages=_footer)
    buffer.seek(0)
    return buffer.getvalue()
