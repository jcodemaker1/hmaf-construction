import csv
import io
from datetime import datetime

import streamlit as st

from model import MODEL_VERSION, calculate_hmaf, one_step_sensitivity
from evidence import (
    PROJECT_COUNT_SCORE,
    TASK_PRESENCE_EVIDENCE,
    TASK_DIGITAL_EFFECTIVENESS,
    matched_context_anchors,
    task_presence_cap,
    workload_message,
    project_value_message,
    activity_message,
    stage_message,
)
from recommendations import allocation_guidance, management_plan
from reporting import build_pdf
from metadata import DEVELOPER_NAME, INSTITUTION

st.set_page_config(page_title="HMAF | Construction Management Allocation", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 3.75rem; padding-bottom: 3rem; max-width: 1450px;}
h1, h2, h3 {color:#18324A;}
.hmaf-eyebrow {color:#147D73;font-weight:700;letter-spacing:.04em;text-transform:uppercase;font-size:.8rem;}
.hmaf-card {border:1px solid #E4E7EC;border-radius:12px;padding:16px 18px;background:#FFFFFF;margin-bottom:10px;}
.hmaf-result {border-left:6px solid #147D73;border-radius:8px;padding:14px 18px;background:#F2F8F7;}
.small-note {color:#667085;font-size:.88rem;}
div[data-baseweb="slider"] [role="slider"] {background-color:#147D73 !important; border-color:#147D73 !important;}
div[data-baseweb="slider"] > div > div > div {background:#147D73 !important;}
</style>
""", unsafe_allow_html=True)

I_ANCHORS = {
    1: "Very low — direct site observation is essential and digital information alone is insufficient.",
    2: "Low — digital information helps, but substantial direct clarification or observation remains necessary.",
    3: "Moderate — the activity is partly information-based and partly dependent on site/contextual input.",
    4: "High — most of the activity can be represented, reviewed and progressed through reliable digital information.",
    5: "Very high — the activity is strongly information-oriented and can be managed almost entirely through current digital information.",
}
READY_ANCHORS = {1:"Very poor / unreliable",2:"Below adequate",3:"Adequate / mixed",4:"Reliable",5:"Highly reliable / consistently available"}
R_ANCHORS = {
    1:"Very low — routine and reversible, with minor consequences.",2:"Low — limited consequence and generally correctable.",3:"Moderate — meaningful programme, quality, commercial or coordination consequences.",4:"High — significant safety, quality, compliance, programme or commercial consequence.",5:"Very high — safety-critical, regulatory, irreversible or otherwise severe consequence.",
}
V_ANCHORS = {
    1:"Very low — no direct physical verification is normally required.",2:"Low — occasional physical confirmation is useful but not central.",3:"Moderate — digital evidence is useful, but site verification materially improves confidence.",4:"High — direct inspection or contextual observation is normally required.",5:"Very high — physical verification, hold-point inspection or direct observation is essential.",
}
L_ANCHORS = {
    1:"Very low — transactional/administrative with minimal interpersonal dependence.",2:"Low — limited relationship or communication complexity.",3:"Moderate — stakeholder/trade interaction matters but can often be supported remotely.",4:"High — trust, mentoring, negotiation, difficult conversation or interpersonal judgement is important.",5:"Very high — leadership, culture, conflict resolution or reading interpersonal cues is central.",
}

HELP = {
    "I": "INFORMATION SUITABILITY (I): Rate whether this specific activity can be accurately understood, reviewed and progressed using current digital information without being physically onsite. Consider drawings, models, photos, dashboards, RFIs, programmes and other digital records. Score 1 where direct site observation is essential; score 5 where digital information is sufficient for almost all management needs. A higher score increases Digital Suitability and moves HMOS toward digital management.",
    "devices": "SUITABLE DEVICES / ACCESS: Rate whether the people who need to manage this activity have appropriate hardware, software access, permissions and usable field devices. Score 1 where access is unreliable or unavailable; score 5 where access is consistently fit for purpose. This contributes to Digital Environment Reliability (D).",
    "connectivity": "SITE NETWORK / CONNECTIVITY: Rate whether internet, mobile or network connectivity is dependable enough to use the required digital systems when and where decisions are made. Score 1 for frequent failure or unusable access; score 5 for consistently reliable connectivity. This contributes to D.",
    "information_quality": "INFORMATION QUALITY / CURRENCY: Rate whether drawings, models, reports, schedules and other digital records are accurate, current, complete and trusted. Score 1 where information is commonly outdated or inaccurate; score 5 where current information can be relied upon for management decisions. This contributes to D.",
    "integration": "SYSTEM INTEGRATION: Rate how well the project's systems and tools work together. Consider duplicate entry, disconnected platforms, manual transfer and whether there is a reliable source of truth. Score 1 for fragmented systems; score 5 for a highly integrated information environment. This contributes to D.",
    "R": "RISK / CONSEQUENCE (R): Rate the consequence of making this decision incorrectly, too late or without sufficient context. Consider safety, compliance, quality, programme, commercial impact and irreversible work. Score 1 where an error is minor and reversible; score 5 where consequences could be severe or irreversible. A higher score increases Physical Presence Need and moves HMOS toward physical management.",
    "V": "VERIFICATION / SITE CONTEXT (V): Rate how necessary it is to physically observe, inspect or verify actual site conditions before the activity can be managed confidently. Score 1 where digital evidence is normally enough; score 5 where a hold point, physical inspection or direct observation is essential. A higher score increases Physical Presence Need.",
    "L": "LEADERSHIP / RELATIONAL REQUIREMENT (L): Rate how much this activity depends on face-to-face leadership, trust, mentoring, negotiation, conflict resolution, difficult conversations or reading non-verbal cues. Score 1 for a mainly transactional activity; score 5 where human interaction is central to effectiveness. A higher score increases Physical Presence Need.",
}


def anchor_slider(label, key, anchors, help_text):
    value = st.slider(label, 1, 5, 3, 1, key=key, help=help_text)
    st.caption(f"**{value}/5:** {anchors[value]}")
    return value


def gauge_html(score):
    position = max(0, min(100, (score - 1) / 4 * 100))
    return f'''<div style="margin:8px 0 18px 0;"><div style="display:flex;justify-content:space-between;font-size:.85rem;color:#475467;"><span>Mostly physical</span><span>Balanced hybrid</span><span>Mostly digital</span></div><div style="position:relative;height:18px;border-radius:9px;background:linear-gradient(90deg,#B9781D 0%,#D6A55A 28%,#A6B7AE 50%,#5FAEA2 72%,#147D73 100%);"><div style="position:absolute;left:calc({position}% - 7px);top:-5px;width:14px;height:28px;border-radius:4px;background:#18324A;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.35);"></div></div><div style="text-align:center;font-weight:700;margin-top:5px;">HMOS {score:.2f}</div></div>'''


def make_assessment_ref():
    return datetime.now().strftime("HMAF-%Y%m%d-%H%M%S")


def render_bullets(items):
    clean = [x for x in items if x and str(x).strip() and str(x).strip().lower() != "null"]
    if clean:
        st.markdown("\n".join([f"- {item}" for item in clean]))


def reset_assessment():
    for key in list(st.session_state.keys()):
        st.session_state.pop(key, None)


with st.sidebar:
    st.markdown("## HMAF")
    st.caption("Hybrid Management Allocation Framework")
    st.markdown("**Assessment**")
    st.write("1. Define situation")
    st.write("2. Assess HMAF factors")
    st.write("3. Review allocation guidance")
    st.write("4. Download report")
    st.divider()
    st.markdown("**Model**")
    st.write(f"Version {MODEL_VERSION}")
    st.caption("Balanced Hybrid range: 2.85–3.15")
    with st.expander("About & limitations"):
        st.write("Research-derived decision support only. HMAF does not replace statutory obligations, WHS duties, contractual requirements, mandatory inspections, competent supervision or professional judgement.")
        st.caption("Version 0.06 adds transparent context calibration and task safeguards derived from directly matched study findings. These are prototype decision rules requiring future validation.")
        st.caption(f"Developed by {DEVELOPER_NAME} | {INSTITUTION}")

st.markdown('<div class="hmaf-eyebrow">Research-derived construction management decision support</div>', unsafe_allow_html=True)
st.title("🏗️ Hybrid Management Allocation Framework")
st.subheader("HMAF / HMOS Management Allocation Tool")
st.write("Assess the **current management activity or project stage**. HMAF combines factor scores with directly matched research evidence about project workload, project scale, critical stages and tasks requiring physical presence.")
st.info("For best use, reassess when project stage, risk, workload, management activity or digital readiness changes. Whole-project assessments remain preliminary because the study indicates that management requirements change with task and stage.")

st.header("1. Define the management situation")
st.write("These fields are not merely descriptive in V0.06. Where the study provides a directly matched result, the project context is used to calibrate the HMOS or apply a task-specific safeguard.")

c1, c2 = st.columns(2)
with c1:
    assessment_name = st.text_input("Assessment name", key="assessment_name", placeholder="Example: Level 3 concrete pour — Tower A")
    scope = st.radio("Assessment level", ["Current management activity", "Current project stage", "Whole project — preliminary only"], key="scope", help="Choose the level you are assessing. Current activity is preferred for task-specific decisions; current project stage is useful for a stage-wide management allocation. Whole-project results are preliminary because the study found that appropriate onsite presence can change by project stage. This selection changes interpretation, not the numerical HMOS.")
    project_stage = st.selectbox("Current project stage", ["Not specified","Pre-construction / design coordination","Mobilisation / site establishment","Structure","Envelope","Services / fit-out","Commissioning","Handover / close-out","Other"], key="project_stage", help="This records the named construction stage. The study did not estimate separate numeric weights for individual stages such as Structure or Fit-out, so the stage name alone does not change HMOS. Use the high-risk/critical-stage control below when the current stage matches the condition directly tested in the survey.")
    high_risk_critical_stage = st.checkbox("This is currently a high-risk or critical project stage", key="high_risk_critical_stage", help="Select this only when the current stage genuinely involves high-risk work or a critical stage of delivery. The survey directly tested high-risk works or critical stages and found a mean management orientation of 2.40/5, so selecting this applies that study result to the context calibration.")
with c2:
    project_value = st.selectbox("Typical project value", ["Not specified","<$5m","$5m–$50m","$50m–$250m",">$250m","Varies / not applicable"], key="project_value", help="Project value affects context only where the survey directly tested the same situation. Small projects (<$5m) had a mean orientation of 2.33/5 and mid-scale projects ($5m–$50m) 2.89/5. The study did not provide directly matched management-orientation scenarios above $50m, so those bands are recorded but not numerically calibrated.")
    concurrent_projects = st.selectbox("How many projects are you currently managing or coordinating?", ["1","2–3","4–5","6–8","9+"], key="concurrent_projects", help="Concurrent project load now directly contributes to Digital Suitability as C, using the same ordered 1–5 coding used in the study. Higher project count increases the scalability pressure toward digital management. The study also found greater project load was strongly associated with lower reported onsite time (rₛ = -0.672).")
    activity = st.selectbox("Management activity being assessed", list(TASK_PRESENCE_EVIDENCE.keys()), key="activity", help="Select the activity that most closely matches the management decision being assessed. Where the study measured a task-specific physical-presence percentage, HMAF uses that evidence as an operational safeguard. For example, 100% selected safety/high-risk supervision and 93.8% selected critical inspections/hold points as requiring physical presence.")

if scope == "Whole project — preliminary only":
    st.warning("Whole-project assessment selected. Treat the result as preliminary and repeat HMAF for major stages and critical management activities.")

C = PROJECT_COUNT_SCORE[concurrent_projects]
st.info(f"**Concurrent project load contribution:** {concurrent_projects} project(s) gives **C = {C:.0f}/5** in Digital Suitability. This is calculated automatically from the project-count category selected above rather than being a separate subjective slider.")

st.header("2. Assess the HMAF factors")
st.caption("Slider explanations update immediately. Hover over each **?** for a detailed definition, what to consider, and how the factor affects HMOS.")
left, right = st.columns(2)
with left:
    st.subheader("Digital Suitability")
    I = anchor_slider("How digitally manageable is this activity? (I — Information suitability)", "I", I_ANCHORS, HELP["I"])
    st.markdown("### Concurrent project load (C)")
    st.metric("Automatically calculated C", f"{C:.0f}/5")
    st.caption(f"Based on **{concurrent_projects}** concurrent project(s). C is no longer manually rated; it comes directly from the project-count category selected above.")
    st.markdown("### Digital Environment Reliability (D)")
    st.caption("D is calculated from four digital-readiness conditions measured in the research.")
    devices = anchor_slider("Suitable devices / access", "devices", READY_ANCHORS, HELP["devices"])
    connectivity = anchor_slider("Site network / connectivity", "connectivity", READY_ANCHORS, HELP["connectivity"])
    information_quality = anchor_slider("Quality and currency of project information", "information_quality", READY_ANCHORS, HELP["information_quality"])
    integration = anchor_slider("Integration between systems / tools", "integration", READY_ANCHORS, HELP["integration"])
with right:
    st.subheader("Physical Presence Need")
    R = anchor_slider("How serious are the consequences of an incorrect or delayed decision? (R — Risk / consequence)", "R", R_ANCHORS, HELP["R"])
    V = anchor_slider("How necessary is direct observation of actual site conditions? (V — Verification / site context)", "V", V_ANCHORS, HELP["V"])
    L = anchor_slider("How dependent is this activity on face-to-face leadership and human interaction? (L — Leadership / relational requirement)", "L", L_ANCHORS, HELP["L"])
    st.markdown("### Governance & emerging technology")
    ai_used = st.checkbox("AI / automated monitoring outputs are used in this assessment", key="ai_used")
    human_review = accountability = validation = True
    if ai_used:
        human_review = st.checkbox("Human review is retained before consequential action", value=True, key="human_review")
        accountability = st.checkbox("Responsibility for the final decision is clearly assigned", value=True, key="accountability")
        validation = st.checkbox("Source data and automated outputs are validated", value=True, key="validation")

live_D = (devices + connectivity + information_quality + integration) / 4
if live_D < 2.5: d_label = "below-adequate digital environment"
elif live_D >= 4: d_label = "strong digital environment"
else: d_label = "adequate / mixed digital environment"
st.info(f"**Live Digital Environment Reliability:** D = **{live_D:.2f}/5** — {d_label}.")

anchors = matched_context_anchors(project_value, concurrent_projects, activity, high_risk_critical_stage)
context_means = [a["mean"] for a in anchors]
cap = task_presence_cap(activity)

current_signature = (assessment_name,scope,project_stage,high_risk_critical_stage,project_value,concurrent_projects,activity,I,C,devices,connectivity,information_quality,integration,R,V,L,ai_used,human_review,accountability,validation)
stored = st.session_state.get("hmaf_record")
if stored and stored.get("input_signature") != current_signature:
    st.session_state.pop("hmaf_record", None)
    st.warning("Assessment inputs have changed. Click Calculate Management Allocation to produce an updated HMOS.")

confirm = st.checkbox("I confirm that I have reviewed all HMAF factors and the selected scores represent the current project conditions.", value=False, key="confirm")
if st.button("Calculate Management Allocation", type="primary", use_container_width=True):
    if not confirm:
        st.warning("Please confirm that you have reviewed the assessment factors before calculating the HMOS.")
    else:
        result = calculate_hmaf(I,C,devices,connectivity,information_quality,integration,R,V,L,context_means=context_means,task_cap=cap)
        inputs = {"I":I,"C":C,"devices":devices,"connectivity":connectivity,"information_quality":information_quality,"integration":integration,"R":R,"V":V,"L":L}
        assessment = {"assessment_name":assessment_name,"scope":scope,"project_stage":project_stage,"high_risk_critical_stage":high_risk_critical_stage,"project_value":project_value,"concurrent_projects":concurrent_projects,"activity":activity}
        plan = management_plan(inputs,result,activity,ai_used,human_review,accountability,validation)
        messages = [workload_message(concurrent_projects),project_value_message(project_value),activity_message(activity),stage_message(high_risk_critical_stage,project_stage)]
        messages = [m for m in messages if m]
        sensitivity = one_step_sensitivity(inputs,result,context_means=context_means,task_cap=cap)
        st.session_state["hmaf_record"] = {"result":result,"inputs":inputs,"assessment":assessment,"anchors":anchors,"plan":plan,"research_messages":messages,"sensitivity":sensitivity,"assessment_ref":make_assessment_ref(),"ai_used":ai_used,"human_review":human_review,"accountability":accountability,"validation":validation,"input_signature":current_signature}

st.button("Reset assessment", on_click=reset_assessment, use_container_width=True)
record = st.session_state.get("hmaf_record")

if record:
    result, inputs, assessment = record["result"], record["inputs"], record["assessment"]
    anchors, plan, research_messages, sensitivity = record["anchors"], record["plan"], record["research_messages"], record["sensitivity"]
    assessment_ref = record["assessment_ref"]
    st.divider()
    st.header("3. HMAF Allocation Guidance")
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Digital Suitability (DS)", f"{result.digital_suitability:.2f} / 5")
    m2.metric("Physical Presence Need (PPN)", f"{result.physical_presence_need:.2f} / 5")
    m3.metric("Base HMOS", f"{result.base_hmos:.2f} / 5")
    m4.metric("Final HMOS", f"{result.hmos:.2f} / 5")
    st.markdown(gauge_html(result.hmos), unsafe_allow_html=True)
    st.markdown(f'<div class="hmaf-result"><b>{result.orientation.upper()}</b><br>{allocation_guidance(result.orientation_code)}</div>', unsafe_allow_html=True)

    pct = TASK_PRESENCE_EVIDENCE.get(assessment["activity"])
    if pct is not None and pct >= 90:
        st.warning(f"**Operational physical-presence safeguard:** {pct:.1f}% of study respondents identified this activity as requiring physical presence. Physical presence should be retained for the assessed activity regardless of the wider hybrid allocation.")
    elif pct is not None:
        st.info(f"**Task-specific survey evidence:** {pct:.1f}% of study respondents identified this activity as requiring physical presence.")

    if inputs["R"] == 5 and inputs["V"] >= 4:
        st.error("**High-consequence verification trigger:** Risk is 5/5 and verification is at least 4/5. Retain deliberate competent physical presence regardless of the aggregate orientation.")

    if record["ai_used"]:
        if record["human_review"] and record["accountability"] and record["validation"]:
            st.success("**AI governance controls recorded:** human review, decision accountability and source/output validation have been confirmed by the assessor.")
        else:
            st.error("**AI governance action required:** one or more controls are not recorded. Do not increase automation or remote reliance until governance is strengthened.")

    st.subheader("What the study says about your selected context")
    st.caption("These blue messages show the survey evidence relevant to the selections you made. Where a directly matched Q11 situation exists, it also contributes to the context calibration shown below.")
    for msg in research_messages:
        st.info(msg)

    task_extra = TASK_DIGITAL_EFFECTIVENESS.get(assessment["activity"])
    if task_extra:
        st.info(f"**Related comparative task evidence:** the closest measured task was **{task_extra['closest_measured_task']}**, with a mean digital-versus-physical effectiveness score of **{task_extra['mean']:.2f}/5**. {task_extra['note']}")

    st.subheader("How project context influenced the HMOS")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Factor-based HMOS", f"{result.base_hmos:.2f}")
    c2.metric("Research context anchor", f"{result.context_anchor:.2f}" if result.context_anchor is not None else "Not applied")
    c3.metric("After context calibration", f"{result.context_calibrated_hmos:.2f}")
    c4.metric("Final after task safeguard", f"{result.hmos:.2f}")
    if anchors:
        st.write("**Research situations used in the context anchor:**")
        for a in anchors:
            st.write(f"- {a['label']}: observed mean **{a['mean']:.2f}/5**, hybrid category **{a['hybrid']:.1f}%**.")
        st.caption("Context calibration uses two parts factor-based HMOS and one part mean of the directly matched study situations. This is a transparent prototype calibration rule, not a statistically estimated regression weight.")
    else:
        st.caption("No directly matched Q11 project-situation mean applies to the selected context, so the factor-based HMOS is not context-calibrated.")
    if result.task_cap is not None:
        st.caption(f"Task safeguard cap applied: **{result.task_cap:.2f}**. This prevents the aggregate score from becoming more digitally oriented than is consistent with the study's task-specific physical-presence evidence.")

    st.subheader("Management Allocation Plan")
    p1,p2 = st.columns(2)
    with p1:
        st.markdown("#### Manage digitally"); render_bullets(plan["digital"])
        st.markdown("#### Improve / strengthen"); render_bullets(plan["improve"])
    with p2:
        st.markdown("#### Retain onsite"); render_bullets(plan["onsite"])
        st.markdown("#### Reassess when"); render_bullets(plan["reassess"])

    st.subheader("Why this result was produced")
    dcol,pcol = st.columns(2)
    with dcol:
        digital_drivers = sorted([("Information suitability",float(inputs["I"])),("Concurrent project load (C)",float(inputs["C"])),("Digital-system reliability",float(result.digital_reliability))], key=lambda x:x[1], reverse=True)
        st.markdown(f"**Strongest digital driver:** {digital_drivers[0][0]} — {digital_drivers[0][1]:.2f}/5")
        render_bullets([f"{n}: **{v:.2f}/5**" for n,v in digital_drivers])
    with pcol:
        presence_drivers = sorted([("Risk / consequence",float(inputs["R"])),("Verification / site context",float(inputs["V"])),("Leadership / relational requirement",float(inputs["L"]))], key=lambda x:x[1], reverse=True)
        st.markdown(f"**Strongest physical-presence driver:** {presence_drivers[0][0]} — {presence_drivers[0][1]:.2f}/5")
        render_bullets([f"{n}: **{v:.2f}/5**" for n,v in presence_drivers])
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Devices", f"{inputs['devices']}/5"); r2.metric("Connectivity", f"{inputs['connectivity']}/5"); r3.metric("Information quality", f"{inputs['information_quality']}/5"); r4.metric("Integration", f"{inputs['integration']}/5")
    weak = [(n,s) for n,s in [("Devices",inputs["devices"]),("Connectivity",inputs["connectivity"]),("Information quality",inputs["information_quality"]),("Integration",inputs["integration"])] if s < 3]
    if weak: st.warning("**Digital-readiness attention required:** " + ", ".join(f"{n} = {s}/5" for n,s in weak) + ".")

    st.subheader("What could change the model outcome?")
    st.caption("This is a transparent sensitivity check, not a recommendation to manipulate scores. Only change a score when actual project conditions genuinely change.")
    changed = [s for s in sensitivity if s["changed_category"]]
    if changed:
        render_bullets([f"**Category change:** {s['label']}; HMOS would become **{s['new_hmos']:.2f}** ({s['new_orientation']})." for s in changed[:3]])
    else:
        st.write("No single one-point change tested would move this assessment into a different HMOS category.")
        render_bullets([f"{s['label']}; HMOS would become **{s['new_hmos']:.2f}** ({s['new_orientation']})." for s in sensitivity[:3]])

    st.header("4. Download assessment record")
    pdf_bytes = build_pdf(assessment,result,plan,anchors,research_messages,assessment_ref,MODEL_VERSION,inputs,record["ai_used"],record["human_review"],record["accountability"],record["validation"],sensitivity)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (assessment["assessment_name"] or assessment_ref))
    st.download_button("Download HMAF Management Allocation Report (PDF)", data=pdf_bytes, file_name=f"{safe}_{assessment_ref}.pdf", mime="application/pdf", type="primary", use_container_width=True)

    csv_output = io.StringIO(); writer = csv.writer(csv_output)
    writer.writerow(["Assessment reference","Model version","Assessment name","Assessment level","Project stage","High-risk / critical stage","Project value","Concurrent projects","Activity","I","C","Devices","Connectivity","Information quality","Integration","D","R","V","L","DS","PPN","Base HMOS","Context anchor","Context-calibrated HMOS","Task cap","Final HMOS","Orientation","AI / automated monitoring used","Human review","Decision accountability","Data/output validation"])
    writer.writerow([assessment_ref,MODEL_VERSION,assessment["assessment_name"],assessment["scope"],assessment["project_stage"],assessment["high_risk_critical_stage"],assessment["project_value"],assessment["concurrent_projects"],assessment["activity"],inputs["I"],inputs["C"],inputs["devices"],inputs["connectivity"],inputs["information_quality"],inputs["integration"],f"{result.digital_reliability:.3f}",inputs["R"],inputs["V"],inputs["L"],f"{result.digital_suitability:.3f}",f"{result.physical_presence_need:.3f}",f"{result.base_hmos:.3f}",f"{result.context_anchor:.3f}" if result.context_anchor is not None else "",f"{result.context_calibrated_hmos:.3f}",f"{result.task_cap:.3f}" if result.task_cap is not None else "",f"{result.hmos:.3f}",result.orientation,record["ai_used"],record["human_review"] if record["ai_used"] else "N/A",record["accountability"] if record["ai_used"] else "N/A",record["validation"] if record["ai_used"] else "N/A"])
    st.download_button("Download raw assessment data (CSV)", data=csv_output.getvalue(), file_name=f"{safe}_{assessment_ref}.csv", mime="text/csv", use_container_width=True)

    with st.expander("Research basis, model interpretation and limitations"):
        st.markdown("""
**What changed in Version 0.06**

Concurrent project count now directly determines C in Digital Suitability. Directly matched Q11 project situations are used as a contextual orientation anchor, with the factor-based HMOS retaining twice the influence of the context anchor. Task-specific physical-presence evidence can impose a transparent safeguard cap.

**Balanced Hybrid classification**

The Balanced Hybrid band has been narrowed to **2.85–3.15**. Scores below 2.85 are classified as Hybrid Leaning Physical and scores above 3.15 as Hybrid Leaning Digital. This makes directional lean visible sooner without changing the underlying 1–5 HMOS scale.

**Project stage**

The stage name itself is descriptive because the study did not estimate separate numerical weights for Structure, Envelope, Fit-out and other individual stages. A numerical context effect is applied only when the assessor identifies the current stage as **high-risk or critical**, which directly matches a tested survey scenario.

**Context calibration**

Where directly matched study scenarios are available, the Context Orientation Anchor is the mean of those observed scenario means. The context-calibrated score is **(2 × factor-based HMOS + context anchor) / 3**. This is a transparent prototype calibration rule rather than a statistically estimated regression coefficient.

**Task safeguard**

Where a clear majority of respondents identified an activity as requiring physical presence, HMAF prevents the aggregate score from becoming inconsistent with that evidence. These safeguard caps are operational prototype rules and require future validation.

**Decision-support limitation**

HMAF does not replace WHS duties, legislation, statutory inspection requirements, contractual requirements, competent supervision or professional judgement.
""")
    st.caption(f"{assessment_ref} • HMAF Version {MODEL_VERSION}")
