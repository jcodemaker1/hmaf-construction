from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def build_pdf(assessment, result, plan, benchmarks, evidence_lines, assessment_ref, model_version):
    buffer=BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=15*mm,bottomMargin=15*mm,title='HMAF Management Allocation Assessment')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Title2',parent=styles['Title'],fontSize=18,leading=22,textColor=colors.HexColor('#18324A'),alignment=TA_CENTER,spaceAfter=8))
    styles.add(ParagraphStyle(name='H2x',parent=styles['Heading2'],fontSize=12.5,leading=15,textColor=colors.HexColor('#18324A'),spaceBefore=8,spaceAfter=5))
    styles.add(ParagraphStyle(name='BodySmall',parent=styles['BodyText'],fontSize=9,leading=12,spaceAfter=4))
    styles.add(ParagraphStyle(name='SmallGrey',parent=styles['BodyText'],fontSize=7.5,leading=10,textColor=colors.HexColor('#667085')))
    story=[Paragraph('Hybrid Management Allocation Framework',styles['Title2']),Paragraph('HMAF Management Allocation Assessment',styles['Heading2']),Spacer(1,3*mm)]
    meta=[['Assessment reference',assessment_ref],['Model version',f'HMAF {model_version}'],['Assessment name',assessment.get('assessment_name') or 'Not specified'],['Assessment level',assessment['scope']],['Project stage',assessment['project_stage']],['Project value',assessment['project_value']],['Concurrent projects',assessment['concurrent_projects']],['Management activity',assessment['activity']]]
    t=Table(meta,colWidths=[48*mm,120*mm])
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#D0D5DD')),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#F2F4F7')),('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8.5),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    story.append(t)
    story.append(Paragraph('Management allocation result',styles['H2x']))
    rt=Table([['Digital Suitability','Physical Presence Need','HMOS','Allocation guidance'],[f'{result.digital_suitability:.2f}/5',f'{result.physical_presence_need:.2f}/5',f'{result.hmos:.2f}/5',result.orientation]],colWidths=[38*mm,42*mm,28*mm,60*mm])
    rt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#18324A')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('ALIGN',(0,0),(2,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#D0D5DD')),('FONTSIZE',(0,0),(-1,-1),8.2),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.append(rt)
    story.append(Paragraph('Management Allocation Plan',styles['H2x']))
    for heading,key in [('Manage digitally','digital'),('Retain onsite','onsite'),('Improve / strengthen','improve'),('Reassess when','reassess')]:
        story.append(Paragraph(f'<b>{heading}</b>',styles['BodySmall']))
        for item in plan[key]: story.append(Paragraph(f'• {item}',styles['BodySmall']))
    if evidence_lines:
        story.append(Paragraph('Evidence informing this assessment',styles['H2x']))
        for line in evidence_lines: story.append(Paragraph(f'• {line}',styles['BodySmall']))
    if benchmarks:
        story.append(Paragraph('Automatic research benchmarks',styles['H2x']))
        rows=[['Relevant study situation','Observed mean /5','Hybrid category']]+[[b['label'],f"{b['mean']:.2f}",f"{b['hybrid']:.1f}%"] for b in benchmarks]
        bt=Table(rows,colWidths=[90*mm,38*mm,40*mm])
        bt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8F1F5')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#D0D5DD')),('FONTSIZE',(0,0),(-1,-1),8.3),('VALIGN',(0,0),(-1,-1),'TOP')]))
        story.append(bt)
    story.append(Paragraph('Important limitations',styles['H2x']))
    story.append(Paragraph('The HMAF/HMOS is a research-derived decision-support model, not a validated predictive equation. It does not replace WHS duties, statutory obligations, contractual requirements, mandatory inspections, competent supervision or professional judgement. Equal weighting is retained at this prototype stage because the study does not estimate validated coefficients for all six HMAF factors. HMOS must not be interpreted as a fixed onsite-attendance percentage.',styles['BodySmall']))
    story.append(Spacer(1,3*mm)); story.append(Paragraph(f"Generated {datetime.now().strftime('%d %B %Y %H:%M')} • {assessment_ref} • HMAF {model_version}",styles['SmallGrey']))
    doc.build(story); buffer.seek(0); return buffer.getvalue()
