import csv
import io
from datetime import datetime

import streamlit as st

from model import MODEL_VERSION, calculate_hmaf, one_step_sensitivity
from evidence import TASK_PRESENCE_EVIDENCE, RESEARCH_FACTS, automatic_benchmarks
from recommendations import allocation_guidance, management_plan
from reporting import build_pdf
from metadata import DEVELOPER_NAME, RESEARCH_PAPER_TITLE, INSTITUTION

st.set_page_config(
    page_title="HMAF | Construction Management Allocation",
    page_icon="🏗️",
    layout="wide",
)

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
    1: "Very low — the activity cannot be accurately understood or progressed through digital information alone.",
    2: "Low — digital information helps, but substantial direct clarification or observation remains necessary.",
    3: "Moderate — the activity is partly information-based and partly dependent on site/contextual input.",
    4: "High — most of the activity can be represented, reviewed and progressed through reliable digital information.",
    5: "Very high — the activity is strongly information-oriented and can be managed almost entirely through current digital information.",
}
C_ANCHORS = {
    1: "Very low — one project/location and physical coverage is practical.",
    2: "Low — limited concurrency or geographic spread.",
    3: "Moderate — several workstreams or locations require some remote coordination.",
    4: "High — multiple projects, teams or locations make continuous physical attendance inefficient.",
    5: "Very high — portfolio/geographic spread makes digital coordination essential to maintain management reach.",
}
READY_ANCHORS = {
    1: "Very poor / unreliable",
    2: "Below adequate",
    3: "Adequate / mixed",
    4: "Reliable",
    5: "Highly reliable / consistently available",
}
R_ANCHORS = {
    1: "Very low — routine and reversible, with minor consequences.",
    2: "Low — limited consequence and generally correctable.",
    3: "Moderate — meaningful programme, quality, commercial or coordination consequences.",
    4: "High — significant safety, quality, compliance, programme or commercial consequence.",
    5: "Very high — safety-critical, regulatory, irreversible or otherwise severe consequence.",
}
V_ANCHORS = {
    1: "Very low — no direct physical verification is normally required.",
    2: "Low — occasional physical confirmation is useful but not central.",
    3: "Moderate — digital evidence is useful, but site verification materially improves confidence.",
    4: "High — direct inspection or contextual observation is normally required.",
    5: "Very high — physical verification, hold-point inspection or direct observation is essential.",
}
L_ANCHORS = {
    1: "Very low — transactional/administrative with minimal interpersonal dependence.",
    2: "Low — limited relationship or communication complexity.",
    3: "Moderate — stakeholder/trade interaction matters but can often be supported remotely.",
    4: "High — trust, mentoring, negotiation, difficult conversation or interpersonal judgement is important.",
    5: "Very high — leadership, culture, conflict resolution or reading interpersonal cues is central.",
}

def anchor_slider(label, key, anchors, help_text):
    value = st.slider(label, 1, 5, 3, 1, key=key, help=help_text)
    st.caption(f"**{value}/5:** {anchors[value]}")
    return value

def gauge_html(score):
    position = max(0, min(100, (score - 1) / 4 * 100))
    return f"""
    <div style="margin:8px 0 18px 0;">
      <div style="display:flex;justify-content:space-between;font-size:.85rem;color:#475467;">
        <span>Mostly physical</span><span>Balanced hybrid</span><span>Mostly digital</span>
      </div>
      <div style="position:relative;height:18px;border-radius:9px;
        background:linear-gradient(90deg,#B9781D 0%,#D6A55A 28%,#A6B7AE 50%,#5FAEA2 72%,#147D73 100%);">
        <div style="position:absolute;left:calc({position}% - 7px);top:-5px;width:14px;height:28px;
          border-radius:4px;background:#18324A;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.35);"></div>
      </div>
      <div style="text-align:center;font-weight:700;margin-top:5px;">HMOS {score:.2f}</div>
    </div>
    """

def make_assessment_ref():
    return datetime.now().strftime("HMAF-%Y%m%d-%H%M%S")

def render_bullets(items):
    clean = [x for x in items if x and str(x).strip() and str(x).strip().lower() != "null"]
    if not clean:
        return
    md = "\n".join([f"- {item}" for item in clean])
    st.markdown(md)

def benchmark_relationship(delta):
    if abs(delta) < 0.05:
        return "Broadly aligned with the study benchmark"
    if delta > 0:
        return f"{abs(delta):.2f} points more digitally oriented than the study benchmark"
    return f"{abs(delta):.2f} points more physically oriented than the study benchmark"

def reset_assessment():
    keys = [
        "assessment_name", "scope", "project_stage", "project_value", "concurrent_projects", "activity",
        "I", "C", "devices", "connectivity", "information_quality", "integration", "R", "V", "L",
        "ai_used", "human_review", "accountability", "validation", "confirm", "hmaf_record"
    ]
    for key in keys:
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
    with st.expander("About & limitations"):
        st.write(
            "Research-derived decision support only. HMAF does not replace statutory obligations, WHS duties, "
            "contractual requirements, mandatory inspections, competent supervision or professional judgement."
        )
        st.caption(
            "The app does not write assessment inputs to a database. A record is created only when the user downloads it."
        )
        st.caption(f"Developed by {DEVELOPER_NAME} | {INSTITUTION}")

st.markdown('<div class="hmaf-eyebrow">Research-derived construction management decision support</div>', unsafe_allow_html=True)
st.title("🏗️ Hybrid Management Allocation Framework")
st.subheader("HMAF / HMOS Management Allocation Tool")
st.write(
    "Assess the **current management activity or project stage**. HMAF combines digital suitability, "
    "physical-presence need and research-derived safeguards to provide transparent allocation guidance."
)
st.info(
    "For best use, reassess the framework when project stage, risk, workload or digital readiness changes. "
    "Whole-project assessments are preliminary because the underlying research indicates that management requirements change by context and stage."
)

with st.expander("How the HMAF calculation works"):
    st.latex(r"D = \frac{Devices + Connectivity + Information\ Quality + Integration}{4}")
    st.latex(r"DS = \frac{I + C + D}{3}")
    st.latex(r"PPN = \frac{R + V + L}{3}")
    st.latex(r"HMOS = 3 + \frac{DS - PPN}{2}")
    st.write(
        "The continuous HMOS remains on the same 1–5 management-orientation continuum used in the underlying study. "
        "Equal weighting is intentionally retained at prototype stage because the research does not estimate validated coefficients for all six HMAF factors."
    )

st.header("1. Define the management situation")
st.write("Enter the conditions that exist now. Research benchmarks are selected automatically from your factual inputs.")

c1, c2 = st.columns(2)
with c1:
    assessment_name = st.text_input("Assessment name", key="assessment_name", placeholder="Example: Level 3 concrete pour — Tower A")
    scope = st.radio(
        "Assessment level",
        ["Current management activity", "Current project stage", "Whole project — preliminary only"],
        key="scope",
        help="Stage/activity assessment is preferred because the research indicates management requirements change with context."
    )
    project_stage = st.selectbox(
        "Current project stage",
        [
            "Not specified",
            "Pre-construction / design coordination",
            "Mobilisation / site establishment",
            "Structure",
            "Envelope",
            "Services / fit-out",
            "Commissioning",
            "Handover / close-out",
            "Other",
        ],
        key="project_stage",
    )
with c2:
    project_value = st.selectbox(
        "Typical project value",
        ["Not specified", "<$5m", "$5m–$50m", "$50m–$250m", ">$250m", "Varies / not applicable"],
        key="project_value",
    )
    concurrent_projects = st.selectbox(
        "How many projects are you currently managing or coordinating?",
        ["Not specified", "1", "2–3", "4–5", "6–8", "9+"],
        key="concurrent_projects",
    )
    activity = st.selectbox("Management activity being assessed", list(TASK_PRESENCE_EVIDENCE.keys()), key="activity")

if scope == "Whole project — preliminary only":
    st.warning(
        "Whole-project assessment selected. Treat the resulting HMOS as preliminary and repeat the assessment for important project stages and management activities."
    )

st.header("2. Assess the HMAF factors")
st.caption("Slider explanations update immediately. No HMOS result is produced until you confirm and click Calculate Management Allocation.")

left, right = st.columns(2)
with left:
    st.subheader("Digital Suitability")
    I = anchor_slider(
        "How digitally manageable is this activity? (I — Information suitability)",
        "I", I_ANCHORS,
        "To what extent can the activity be accurately understood, reviewed and progressed using current digital information?"
    )
    C = anchor_slider(
        "How strongly does workload require remote management reach? (C — Concurrency / scalability)",
        "C", C_ANCHORS,
        "How strongly do concurrent projects, geographic spread or multiple workstreams create a need for digital management reach?"
    )

    st.markdown("### Digital Environment Reliability (D)")
    st.caption("D is calculated from the four digital-readiness conditions measured in the research.")
    devices = anchor_slider("Suitable devices / access", "devices", READY_ANCHORS, "Are suitable devices, access and permissions available?")
    connectivity = anchor_slider("Site network / connectivity", "connectivity", READY_ANCHORS, "Is connectivity dependable enough for the intended digital workflow?")
    information_quality = anchor_slider("Quality and currency of project information", "information_quality", READY_ANCHORS, "Is the information current, accurate and complete enough for management decisions?")
    integration = anchor_slider("Integration between systems / tools", "integration", READY_ANCHORS, "Do the systems operate coherently without excessive duplication or manual re-entry?")

with right:
    st.subheader("Physical Presence Need")
    R = anchor_slider(
        "How serious are the consequences of an incorrect or delayed decision? (R — Risk / consequence)",
        "R", R_ANCHORS,
        "Consider safety, quality, compliance, programme, commercial and irreversible-work consequences."
    )
    V = anchor_slider(
        "How necessary is direct observation of actual site conditions? (V — Verification / site context)",
        "V", V_ANCHORS,
        "Consider inspection, hold points, physical verification and conditions that are difficult to represent digitally."
    )
    L = anchor_slider(
        "How dependent is this activity on face-to-face leadership and human interaction? (L — Leadership / relational requirement)",
        "L", L_ANCHORS,
        "Consider trust, mentoring, difficult conversations, conflict resolution and interpersonal cues."
    )

    st.markdown("### Governance & emerging technology")
    ai_used = st.checkbox("AI / automated monitoring outputs are used in this assessment", key="ai_used")
    human_review = accountability = validation = True
    if ai_used:
        human_review = st.checkbox("Human review is retained before consequential action", value=True, key="human_review")
        accountability = st.checkbox("Responsibility for the final decision is clearly assigned", value=True, key="accountability")
        validation = st.checkbox("Source data and automated outputs are validated", value=True, key="validation")

live_D = (devices + connectivity + information_quality + integration) / 4
live_label = "adequate / mixed digital environment"
if live_D < 2.5:
    live_label = "below-adequate digital environment"
elif live_D >= 4:
    live_label = "strong digital environment"
st.info(f"**Live Digital Environment Reliability:** D = **{live_D:.2f}/5** — {live_label}.")

current_signature = (
    assessment_name, scope, project_stage, project_value, concurrent_projects, activity,
    I, C, devices, connectivity, information_quality, integration, R, V, L, ai_used, human_review, accountability, validation
)
stored = st.session_state.get("hmaf_record")
if stored and stored.get("input_signature") != current_signature:
    st.session_state.pop("hmaf_record", None)
    st.warning("Assessment inputs have changed. Review the updated factors and click Calculate Management Allocation to produce a new HMOS result.")

confirm = st.checkbox(
    "I confirm that I have reviewed all HMAF factors and the selected scores represent the current project conditions.",
    value=False,
    key="confirm"
)

if st.button("Calculate Management Allocation", type="primary", use_container_width=True):
    if not confirm:
        st.warning("Please confirm that you have reviewed the assessment factors before calculating the HMOS.")
    else:
        result = calculate_hmaf(I, C, devices, connectivity, information_quality, integration, R, V, L)
        inputs = {
            "I": I, "C": C, "devices": devices, "connectivity": connectivity,
            "information_quality": information_quality, "integration": integration,
            "R": R, "V": V, "L": L,
        }
        assessment = {
            "assessment_name": assessment_name,
            "scope": scope,
            "project_stage": project_stage,
            "project_value": project_value,
            "concurrent_projects": concurrent_projects,
            "activity": activity,
        }
        benchmarks = automatic_benchmarks(project_value, concurrent_projects, activity)
        plan = management_plan(inputs, result, activity, ai_used, human_review, accountability, validation)
        st.session_state["hmaf_record"] = {
            "result": result,
            "inputs": inputs,
            "assessment": assessment,
            "benchmarks": benchmarks,
            "plan": plan,
            "assessment_ref": make_assessment_ref(),
            "ai_used": ai_used,
            "human_review": human_review,
            "accountability": accountability,
            "validation": validation,
            "input_signature": current_signature,
        }

st.button(
    "Reset assessment",
    on_click=reset_assessment,
    use_container_width=True,
    help="Clear the current assessment and return all HMAF inputs to their default values."
)

record = st.session_state.get("hmaf_record")
if record:
    result = record["result"]
    inputs = record["inputs"]
    assessment = record["assessment"]
    benchmarks = record["benchmarks"]
    plan = record["plan"]
    assessment_ref = record["assessment_ref"]
    activity = assessment["activity"]

    st.divider()
    st.header("3. HMAF Allocation Guidance")

    m1, m2, m3 = st.columns(3)
    m1.metric("Digital Suitability (DS)", f"{result.digital_suitability:.2f} / 5")
    m2.metric("Physical Presence Need (PPN)", f"{result.physical_presence_need:.2f} / 5")
    m3.metric("HMOS", f"{result.hmos:.2f} / 5")

    st.markdown(gauge_html(result.hmos), unsafe_allow_html=True)
    st.markdown(
        f'<div class="hmaf-result"><b>{result.orientation.upper()}</b><br>{allocation_guidance(result.orientation_code)}</div>',
        unsafe_allow_html=True
    )

    evidence_lines = []
    presence_pct = TASK_PRESENCE_EVIDENCE.get(activity)
    if presence_pct is not None:
        evidence_lines.append(f"{presence_pct:.1f}% of study respondents identified {activity.lower()} as requiring physical presence.")
        if presence_pct == 100:
            st.error(
                f"**Critical physical-presence safeguard:** {presence_pct:.1f}% of study respondents selected this activity as requiring physical presence. "
                "Do not use HMOS to justify removing competent onsite supervision."
            )
        else:
            st.warning(
                f"**Research physical-presence signal:** {presence_pct:.1f}% of study respondents selected this activity as requiring physical presence."
            )

    if inputs["R"] == 5 and inputs["V"] >= 4:
        st.error(
            "**High-consequence verification trigger:** Risk is 5/5 and verification is at least 4/5. "
            "Retain deliberate competent physical presence regardless of the aggregate orientation."
        )
        evidence_lines.append("The assessment triggered the HMAF high-consequence verification safeguard (R = 5 and V ≥ 4).")

    if result.digital_reliability < 3:
        readiness = {
            "devices/access": inputs["devices"],
            "connectivity": inputs["connectivity"],
            "information quality": inputs["information_quality"],
            "system integration": inputs["integration"],
        }
        weakest = min(readiness, key=readiness.get)
        st.warning(
            f"**Digital-readiness constraint:** D = {result.digital_reliability:.2f}/5. "
            f"The weakest selected readiness condition is **{weakest} ({readiness[weakest]}/5)**. "
            "Strengthen the digital environment before increasing digital reliance."
        )

    if record["ai_used"]:
        if record["human_review"] and record["accountability"] and record["validation"]:
            st.success("**AI governance gate satisfied:** human review, decision accountability and output validation are all recorded.")
        else:
            st.error(
                "**AI governance gate not satisfied:** one or more safeguards are missing. "
                "Do not use the HMOS to justify increased automation or remote reliance until governance is strengthened."
            )

    if assessment["project_value"] == "$5m–$50m":
        st.info(
            f"**Mid-scale onsite context:** {RESEARCH_FACTS['mid_at_least_31_pct']:.1f}% of valid respondents nominated at least 31% onsite attendance, "
            f"while {RESEARCH_FACTS['mid_stage_dependent_pct']:.1f}% considered one fixed percentage inappropriate because the requirement depended on project stage. "
            "HMAF therefore does not convert HMOS into a fixed onsite percentage."
        )
        evidence_lines.append(
            f"For a typical mid-scale project, {RESEARCH_FACTS['mid_at_least_31_pct']:.1f}% nominated at least 31% onsite attendance and "
            f"{RESEARCH_FACTS['mid_stage_dependent_pct']:.1f}% said the requirement depended too much on stage for one fixed percentage."
        )

    if benchmarks:
        st.subheader("Research benchmarks relevant to this assessment")
        st.caption("Automatically selected from the project context. Benchmarks provide comparison only and do not alter the HMOS.")
        for b in benchmarks:
            delta = result.hmos - b["mean"]
            relationship = benchmark_relationship(delta)
            st.markdown(
                f"""
                <div class="hmaf-card">
                <b>{b['label']}</b><br>
                <span style="color:#667085">Study mean</span> <b>{b['mean']:.2f}/5</b>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <span style="color:#667085">Hybrid category</span> <b>{b['hybrid']:.1f}%</b><br>
                <span style="color:#147D73"><b>{relationship}</b></span><br>
                <span class="small-note">{b['evidence']} Contextual evidence only; not a target.</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.subheader("Management Allocation Plan")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("#### Manage digitally")
        render_bullets(plan.get("digital", []))
        st.markdown("#### Improve / strengthen")
        render_bullets(plan.get("improve", []))
    with p2:
        st.markdown("#### Retain onsite")
        render_bullets(plan.get("onsite", []))
        st.markdown("#### Reassess when")
        render_bullets(plan.get("reassess", []))

    st.subheader("Why this result was produced")
    dcol, pcol = st.columns(2)
    with dcol:
        digital_drivers = sorted([
            ("Information suitability", float(inputs["I"])),
            ("Concurrency / scalability", float(inputs["C"])),
            ("Digital-system reliability", float(result.digital_reliability)),
        ], key=lambda x: x[1], reverse=True)
        st.markdown(f"**Strongest digital driver:** {digital_drivers[0][0]} — {digital_drivers[0][1]:.2f}/5")
        render_bullets([f"{n}: **{v:.2f}/5**" for n, v in digital_drivers])
    with pcol:
        presence_drivers = sorted([
            ("Risk / consequence", float(inputs["R"])),
            ("Verification / site context", float(inputs["V"])),
            ("Leadership / relational requirement", float(inputs["L"])),
        ], key=lambda x: x[1], reverse=True)
        st.markdown(f"**Strongest physical-presence driver:** {presence_drivers[0][0]} — {presence_drivers[0][1]:.2f}/5")
        render_bullets([f"{n}: **{v:.2f}/5**" for n, v in presence_drivers])

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Devices", f"{inputs['devices']}/5")
    r2.metric("Connectivity", f"{inputs['connectivity']}/5")
    r3.metric("Information quality", f"{inputs['information_quality']}/5")
    r4.metric("Integration", f"{inputs['integration']}/5")

    st.subheader("Evidence informing this recommendation")
    if presence_pct is None:
        st.write("The selected activity did not have a direct task-specific physical-presence percentage in the study; the recommendation therefore relies on the HMAF factors and any applicable project-situation benchmarks.")
    render_bullets(evidence_lines)
    st.write(
        f"Physical presence for safety-critical judgement had an RII of **{RESEARCH_FACTS['safety_rII']:.3f}**, "
        f"while digital information visibility and general hybrid effectiveness each had an RII of **{RESEARCH_FACTS['digital_visibility_rII']:.3f}**."
    )
    st.write(
        f"Digital-system reliability was positively associated with perceived digital effectiveness (rₛ = **{RESEARCH_FACTS['digital_reliability_effectiveness_rs']:.3f}**) "
        f"and remained independently associated in the exploratory regression (B = **{RESEARCH_FACTS['digital_reliability_regression_B']:.3f}**, p = **{RESEARCH_FACTS['digital_reliability_regression_p']:.3f}**)."
    )

    st.subheader("What could change the model outcome?")
    st.caption("This is a transparent sensitivity check, not a recommendation to manipulate scores. Only change a score when project conditions genuinely change.")
    sensitivity = one_step_sensitivity(inputs, result)
    changed = [s for s in sensitivity if s["changed_category"]]
    if changed:
        render_bullets([f"**Category change:** {s['label']}, HMOS would become **{s['new_hmos']:.2f}** ({s['new_orientation']})." for s in changed[:3]])
    else:
        st.write("No single one-point change tested would move this assessment into a different HMOS category.")
        render_bullets([f"{s['label']}, HMOS would become **{s['new_hmos']:.2f}** ({s['new_orientation']})." for s in sensitivity[:3]])

    st.header("4. Download assessment record")
    pdf_bytes = build_pdf(
        assessment,
        result,
        plan,
        benchmarks,
        evidence_lines,
        assessment_ref,
        MODEL_VERSION,
        inputs,
        record["ai_used"],
        record["human_review"],
        record["accountability"],
        record["validation"],
        sensitivity,
    )
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in (assessment["assessment_name"] or assessment_ref))
    st.download_button(
        "Download HMAF Management Allocation Report (PDF)",
        data=pdf_bytes,
        file_name=f"{safe}_{assessment_ref}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

    csv_output = io.StringIO()
    writer = csv.writer(csv_output)
    writer.writerow([
        "Assessment reference", "Model version", "Assessment name", "Assessment level", "Project stage",
        "Project value", "Concurrent projects", "Activity", "I", "C", "Devices", "Connectivity",
        "Information quality", "Integration", "D", "R", "V", "L", "DS", "PPN", "HMOS", "Orientation",
        "AI / automated monitoring used", "Human review", "Decision accountability", "Data/output validation"
    ])
    writer.writerow([
        assessment_ref, MODEL_VERSION, assessment["assessment_name"], assessment["scope"],
        assessment["project_stage"], assessment["project_value"], assessment["concurrent_projects"],
        assessment["activity"], inputs["I"], inputs["C"], inputs["devices"], inputs["connectivity"],
        inputs["information_quality"], inputs["integration"], f"{result.digital_reliability:.3f}",
        inputs["R"], inputs["V"], inputs["L"], f"{result.digital_suitability:.3f}",
        f"{result.physical_presence_need:.3f}", f"{result.hmos:.3f}", result.orientation,
        record["ai_used"],
        record["human_review"] if record["ai_used"] else "N/A",
        record["accountability"] if record["ai_used"] else "N/A",
        record["validation"] if record["ai_used"] else "N/A"
    ])
    st.download_button(
        "Download raw assessment data (CSV)",
        data=csv_output.getvalue(),
        file_name=f"{safe}_{assessment_ref}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    with st.expander("Research basis, model interpretation and limitations"):
        st.markdown(
            """
**Interpretation**

HMAF is intended to be recalculated by management activity or project stage. It does not translate HMOS into a fixed onsite-attendance percentage.

**Equal weighting**

Equal weights remain intentional in Version 0.05. The research supports the inclusion and expected direction of the six HMAF factors, but it does not estimate defensible coefficients for all six factors in the final allocation equation. The exploratory regression coefficient for digital-system reliability is not inserted as an HMOS weight because that regression predicted perceived digital effectiveness rather than the final digital/physical allocation outcome.

**PPN interpretation**

PPN is an operational allocation index. It is not claimed to be a validated psychometric scale combining safety, verification and relational leadership into one interchangeable construct. Strong physical-presence signals remain visible separately.

**Decision-support limitation**

HMAF does not replace WHS duties, legislation, statutory inspection requirements, contractual requirements, competent supervision or professional judgement.
            """
        )

    st.caption(f"{assessment_ref} • HMAF Version {MODEL_VERSION}")
