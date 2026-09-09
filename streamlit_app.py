import csv
import io
from datetime import datetime

import streamlit as st

st.set_page_config(
    page_title="HMAF | Hybrid Management Allocation Framework",
    page_icon="🏗️",
    layout="wide",
)

# ============================================================
# RESEARCH-DERIVED REFERENCE DATA
# ============================================================

SCENARIO_BENCHMARKS = {
    "None selected": None,
    "Routine reporting / coordination": {"mean": 3.70, "hybrid": 70.0},
    "Managing four or more projects": {"mean": 3.60, "hybrid": 86.7},
    "Mid-scale project ($5m–$50m)": {"mean": 2.89, "hybrid": 82.1},
    "High-risk works / critical stage": {"mean": 2.40, "hybrid": 63.3},
    "Small project (<$5m)": {"mean": 2.33, "hybrid": 78.8},
}

TASK_PRESENCE_EVIDENCE = {
    "Routine reporting / document coordination": None,
    "Safety walk / high-risk work supervision": 100.0,
    "Critical inspection / hold point": 93.8,
    "Quality / rework inspection": 87.5,
    "Client / stakeholder walk-through": 84.4,
    "Difficult conversation": 75.0,
    "Mentoring / coaching": 71.9,
    "Conflict resolution": 68.8,
    "Complex trade coordination": 68.8,
    "Reading site conditions before a decision": 68.8,
    "Other / custom activity": None,
}

I_ANCHORS = {
    1: "Very low — the task cannot be represented or progressed reliably through digital information.",
    2: "Low — digital information helps, but substantial direct clarification or observation is still required.",
    3: "Moderate — the task is partly information-based and partly dependent on site/contextual input.",
    4: "High — most of the task can be represented, reviewed and progressed through reliable digital information.",
    5: "Very high — the task is strongly information-oriented and can be managed almost entirely through current digital information.",
}

C_ANCHORS = {
    1: "Very low — one project/location; continuous physical coverage is practical.",
    2: "Low — limited concurrency or geographic spread; physical attendance remains easy to maintain.",
    3: "Moderate — several workstreams/locations require some remote coordination.",
    4: "High — multiple projects, teams or locations make continuous physical attendance inefficient.",
    5: "Very high — extensive portfolio/geographic spread makes digital coordination essential to maintain management reach.",
}

READINESS_ANCHORS = {
    1: "Very poor / unreliable",
    2: "Below adequate",
    3: "Adequate / mixed",
    4: "Reliable",
    5: "Highly reliable / consistently available",
}

R_ANCHORS = {
    1: "Very low — routine and reversible; errors have minor consequences.",
    2: "Low — limited consequence; issues can usually be corrected without major impact.",
    3: "Moderate — meaningful programme, quality, commercial or coordination consequences.",
    4: "High — significant safety, quality, compliance, programme or commercial consequence.",
    5: "Very high — safety-critical, regulatory, irreversible or otherwise severe consequence.",
}

V_ANCHORS = {
    1: "Very low — no direct physical verification is normally required.",
    2: "Low — occasional physical confirmation is useful but not central.",
    3: "Moderate — digital evidence is useful, but site verification materially improves confidence.",
    4: "High — direct inspection or contextual observation is normally required.",
    5: "Very high — physical verification, a hold-point inspection or direct observation is essential.",
}

L_ANCHORS = {
    1: "Very low — transactional/administrative task with minimal interpersonal dependence.",
    2: "Low — limited relationship or communication complexity.",
    3: "Moderate — stakeholder/trade interaction matters, but can often be supported remotely.",
    4: "High — trust, mentoring, negotiation, difficult conversation or interpersonal judgement is important.",
    5: "Very high — leadership, culture, conflict resolution or reading interpersonal cues is central.",
}


# ============================================================
# FUNCTIONS
# ============================================================

def scored_slider(label, key, anchors, help_text, default=3):
    value = st.slider(
        label,
        min_value=1,
        max_value=5,
        value=default,
        step=1,
        key=key,
        help=help_text,
    )
    st.caption(f"**Selected {value}/5:** {anchors[value]}")
    return value


def classify_hmos(score):
    # Half-point boundaries map the continuous score back to the original
    # five management-orientation categories used in the research.
    if score < 1.5:
        return "Mostly physical presence", "physical"
    if score < 2.5:
        return "Hybrid leaning physical", "hybrid_physical"
    if score < 3.5:
        return "Balanced hybrid", "balanced"
    if score < 4.5:
        return "Hybrid leaning digital", "hybrid_digital"
    return "Mostly digital tools", "digital"


def orientation_advice(code):
    return {
        "physical": (
            "Base management around direct onsite engagement. Use digital tools for documentation, "
            "scheduling, information sharing and traceability, but not as a substitute for direct "
            "observation and leadership."
        ),
        "hybrid_physical": (
            "Use a hybrid approach with protected physical presence. Allocate routine information "
            "processing and suitable coordination digitally, while retaining regular onsite coverage "
            "for verification, risk decisions, trade interfaces and relational leadership."
        ),
        "balanced": (
            "Use a deliberately balanced hybrid approach. Separate information-oriented work from "
            "safety-, verification- and relationship-dependent work, and reassess when project conditions change."
        ),
        "hybrid_digital": (
            "Use a digital-leaning hybrid approach. Manage routine coordination, reporting and information "
            "flow digitally, while scheduling targeted onsite interventions for inspections, high-consequence "
            "decisions, stakeholder engagement and emerging site issues."
        ),
        "digital": (
            "A digital-first allocation may be appropriate for the assessed activity if the digital "
            "environment is reliable and no strong physical-presence trigger applies. Retain escalation "
            "points, periodic verification and accountable human review."
        ),
    }[code]


def gauge_html(score):
    position = max(0, min(100, (score - 1) / 4 * 100))
    return f"""
    <div style="margin:8px 0 18px 0;">
      <div style="display:flex;justify-content:space-between;font-size:.85rem;color:#475569;">
        <span>Mostly physical</span><span>Balanced hybrid</span><span>Mostly digital</span>
      </div>
      <div style="position:relative;height:18px;border-radius:9px;
        background:linear-gradient(90deg,#9a3412 0%,#f59e0b 35%,#d1d5db 50%,#38bdf8 70%,#1d4ed8 100%);">
        <div style="position:absolute;left:calc({position}% - 7px);top:-5px;width:14px;height:28px;
          border-radius:4px;background:#111827;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.35);">
        </div>
      </div>
      <div style="text-align:center;font-weight:700;margin-top:5px;">HMOS {score:.2f}</div>
    </div>
    """


# ============================================================
# PAGE INTRODUCTION
# ============================================================

st.title("🏗️ Hybrid Management Allocation Framework")
st.subheader("HMOS Decision-Support Tool for Construction Project Management")

st.info(
    "Assess one project, project stage or management activity at a time. "
    "The model calculates the Hybrid Management Orientation Score (HMOS) in the background "
    "and returns a management-allocation recommendation."
)

with st.sidebar:
    st.header("Model status")
    st.write("**HMAF / HMOS research prototype — v0.1**")
    st.warning(
        "Decision support only. It does not replace statutory obligations, WHS requirements, "
        "contractual requirements, mandatory inspections or competent professional judgement."
    )
    st.caption(
        "The app code does not write your assessment inputs to a database or file. "
        "A record is created only if you choose to download it."
    )

with st.expander("Show the calculation", expanded=False):
    st.latex(r"DS = \frac{I + C + D}{3}")
    st.latex(r"D = \frac{Devices + Connectivity + Information\ Quality + Integration}{4}")
    st.latex(r"PPN = \frac{R + V + L}{3}")
    st.latex(r"HMOS = 3 + \frac{DS - PPN}{2}")
    st.write(
        "DS = Digital Suitability. PPN = Physical Presence Need. "
        "The continuous HMOS remains on the same theoretical 1–5 orientation scale used in the research."
    )
    st.write(
        "Equal weighting is intentional at prototype stage. The study supports the inclusion and direction "
        "of the factors, but it does not provide validated coefficients for weighting all six HMAF variables."
    )

# ============================================================
# 1. CONTEXT
# ============================================================

st.header("1. Assessment context")

c1, c2 = st.columns(2)
with c1:
    assessment_name = st.text_input(
        "Assessment name",
        placeholder="Example: Level 3 concrete pour — Tower A",
    )
    scope = st.selectbox(
        "What are you assessing?",
        ["Management task / activity", "Project stage", "Whole project"],
    )
    project_stage = st.selectbox(
        "Project stage",
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
    )

with c2:
    project_value = st.selectbox(
        "Typical project value",
        ["Not specified", "<$5m", "$5m–$50m", "$50m–$250m", ">$250m", "Varies / not applicable"],
    )
    task = st.selectbox(
        "Closest management activity",
        list(TASK_PRESENCE_EVIDENCE.keys()),
    )
    benchmark_name = st.selectbox(
        "Closest research project-situation benchmark",
        list(SCENARIO_BENCHMARKS.keys()),
    )

st.caption(
    "Context selections are shown in the output and used for research comparison. "
    "They do not secretly change the HMOS calculation."
)

# ============================================================
# 2. HMAF INPUTS
# ============================================================

st.header("2. Score the HMAF factors")
st.write("Score the conditions that exist **now**. Use the written anchors rather than guessing from the number alone.")

left, right = st.columns(2)

with left:
    st.subheader("Digital Suitability")

    I = scored_slider(
        "I — Information suitability",
        "I",
        I_ANCHORS,
        "How readily can the activity be represented, reviewed and progressed through reliable digital information?",
    )

    C = scored_slider(
        "C — Concurrency / scalability requirement",
        "C",
        C_ANCHORS,
        "How strongly does workload, portfolio scale or geographic spread create a need for digital management reach?",
    )

    st.markdown("#### D — Digital-system reliability")
    st.caption(
        "D is calculated automatically from the four digital-readiness conditions measured in the research."
    )

    device = scored_slider(
        "Suitable devices / access",
        "device",
        READINESS_ANCHORS,
        "Are suitable devices and system access available to the people who need them?",
    )
    connectivity = scored_slider(
        "Site network / connectivity",
        "connectivity",
        READINESS_ANCHORS,
        "Is connectivity dependable enough for the intended digital workflow?",
    )
    info_quality = scored_slider(
        "Quality and currency of project information",
        "info_quality",
        READINESS_ANCHORS,
        "Is the digital information accurate, current and complete enough for management decisions?",
    )
    integration = scored_slider(
        "Integration between systems / tools",
        "integration",
        READINESS_ANCHORS,
        "Do the systems operate as a coherent information environment rather than disconnected platforms?",
    )

with right:
    st.subheader("Physical Presence Need")

    R = scored_slider(
        "R — Risk / consequence",
        "R",
        R_ANCHORS,
        "What is the consequence if the decision is delayed, incorrect or made without sufficient context?",
    )
    V = scored_slider(
        "V — Verification / site context",
        "V",
        V_ANCHORS,
        "How strongly does the activity require direct inspection, observation or confirmation of actual site conditions?",
    )
    L = scored_slider(
        "L — Leadership / relational requirement",
        "L",
        L_ANCHORS,
        "How much does effectiveness depend on trust, face-to-face communication, mentoring, conflict resolution or interpersonal judgement?",
    )

    st.markdown("#### Governance and emerging-technology safeguard")
    ai_used = st.checkbox("AI / automated monitoring outputs are used in this assessment")

    human_review = True
    accountability = True
    validation = True

    if ai_used:
        human_review = st.checkbox("Human review is retained before consequential action", value=True)
        accountability = st.checkbox("Responsibility for the final decision is clearly assigned", value=True)
        validation = st.checkbox("Data / automated outputs are validated", value=True)

# ============================================================
# 3. CALCULATIONS
# ============================================================

D = (device + connectivity + info_quality + integration) / 4
DS = (I + C + D) / 3
PPN = (R + V + L) / 3
HMOS = 3 + ((DS - PPN) / 2)
HMOS = max(1.0, min(5.0, HMOS))

orientation, orientation_code = classify_hmos(HMOS)

# ============================================================
# 4. RESULT
# ============================================================

st.header("3. Management allocation result")

m1, m2, m3 = st.columns(3)
m1.metric("Digital Suitability (DS)", f"{DS:.2f} / 5")
m2.metric("Physical Presence Need (PPN)", f"{PPN:.2f} / 5")
m3.metric("HMOS", f"{HMOS:.2f} / 5")

st.markdown(gauge_html(HMOS), unsafe_allow_html=True)

st.success(f"**Recommended orientation: {orientation}**")
st.write(orientation_advice(orientation_code))

# Digital-readiness safeguard
if D < 3:
    st.warning(
        f"**Digital-readiness constraint:** D = {D:.2f}, below the neutral/adequate point of 3. "
        "Address the weak readiness conditions before increasing digital reliance."
    )

# Empirical physical-presence safeguard
presence_pct = TASK_PRESENCE_EVIDENCE.get(task)
if presence_pct is not None:
    if presence_pct == 100.0:
        st.error(
            f"**Critical physical-presence safeguard:** {presence_pct:.1f}% of study respondents selected this activity "
            "as requiring physical presence. Do not use the HMOS to justify removing competent onsite supervision."
        )
    else:
        st.warning(
            f"**Research presence benchmark:** {presence_pct:.1f}% of study respondents selected this activity "
            "as requiring physical presence. Treat this as an empirical presence signal alongside the HMOS."
        )

# Additional consequence/verification safeguard
if R == 5 and V >= 4:
    st.error(
        "**High-consequence verification trigger:** risk is 5/5 and verification is at least 4/5. "
        "The activity requires deliberate competent physical presence even if the overall HMOS leans digital."
    )

# AI governance safeguard
if ai_used:
    if human_review and accountability and validation:
        st.success("**Governance gate satisfied:** human review, clear accountability and validation are recorded.")
    else:
        st.error(
            "**Governance gate not satisfied:** one or more safeguards are missing. "
            "Do not use the HMOS to justify increased automation or remote reliance until governance is strengthened."
        )

# Research project-situation comparison
benchmark = SCENARIO_BENCHMARKS.get(benchmark_name)
if benchmark:
    delta = HMOS - benchmark["mean"]
    st.info(
        f"**Research benchmark — {benchmark_name}:** observed mean orientation = {benchmark['mean']:.2f}/5; "
        f"{benchmark['hybrid']:.1f}% selected a hybrid category. "
        f"Your HMOS is {delta:+.2f} points from that observed mean. This comparison is contextual evidence, not a target."
    )

# Mid-scale attendance context
if project_value == "$5m–$50m":
    st.info(
        "**Mid-scale onsite benchmark:** 46.9% of valid respondents nominated at least 31% onsite attendance, "
        "while 25.0% said one fixed percentage was inappropriate because the requirement depended on project stage. "
        "The HMOS therefore does not convert the score into a fixed onsite percentage."
    )

# ============================================================
# 5. EXPLAINABILITY
# ============================================================

st.header("4. Why this result was produced")

digital_drivers = sorted(
    [
        ("Information suitability", float(I)),
        ("Concurrency / scalability", float(C)),
        ("Digital-system reliability", float(D)),
    ],
    key=lambda x: x[1],
    reverse=True,
)

presence_drivers = sorted(
    [
        ("Risk / consequence", float(R)),
        ("Verification / site context", float(V)),
        ("Leadership / relational requirement", float(L)),
    ],
    key=lambda x: x[1],
    reverse=True,
)

e1, e2 = st.columns(2)
with e1:
    st.markdown("#### Digital drivers")
    for name, value in digital_drivers:
        st.write(f"- **{name}: {value:.2f}/5**")
with e2:
    st.markdown("#### Physical-presence drivers")
    for name, value in presence_drivers:
        st.write(f"- **{name}: {value:.2f}/5**")

st.markdown("#### Digital-readiness breakdown")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Devices", f"{device}/5")
r2.metric("Connectivity", f"{connectivity}/5")
r3.metric("Information quality", f"{info_quality}/5")
r4.metric("Integration", f"{integration}/5")

st.markdown("#### Recommended management actions")
actions = []

if I >= 4:
    actions.append("Use digital workflows for information capture, document control, programme/reporting and routine coordination.")
if C >= 4:
    actions.append("Use dashboards, standardised reporting and clear site-delegate/escalation arrangements to maintain reach across projects or locations.")
if device < 3:
    actions.append("Improve access to suitable devices before increasing digital reliance.")
if connectivity < 3:
    actions.append("Resolve site connectivity or provide a reliable offline/synchronisation process.")
if info_quality < 3:
    actions.append("Strengthen information ownership, update frequency and quality control.")
if integration < 3:
    actions.append("Reduce duplicated systems/manual re-entry and improve interoperability or the single-source-of-truth process.")
if R >= 4:
    actions.append("Define a competent onsite decision-maker and escalation path for high-consequence decisions.")
if V >= 4:
    actions.append("Schedule direct physical inspection/verification at relevant hold points or before irreversible work proceeds.")
if L >= 4:
    actions.append("Use face-to-face engagement for leadership, mentoring, conflict resolution, difficult conversations or trust-building.")

if ai_used and not human_review:
    actions.append("Add mandatory human review for AI/automated outputs.")
if ai_used and not accountability:
    actions.append("Assign clear decision accountability for actions informed by AI/automated outputs.")
if ai_used and not validation:
    actions.append("Implement data/output validation for AI/automated monitoring.")

if not actions:
    actions.append(
        "Maintain the current allocation, monitor changing project conditions, and recalculate the HMOS when stage, risk, workload or digital readiness changes."
    )

for action in actions:
    st.write(f"- {action}")

st.info(
    "Recalculate the HMOS whenever the project moves into a different stage, the risk profile changes, "
    "a new hold point is reached, concurrent workload changes, or the digital information environment materially changes."
)

# ============================================================
# 6. DOWNLOADABLE AUDIT TRAIL
# ============================================================

st.header("5. Download assessment record")

output = io.StringIO()
writer = csv.writer(output)
writer.writerow([
    "Timestamp", "Assessment name", "Scope", "Project stage", "Project value", "Task",
    "Research benchmark", "I", "C", "Devices", "Connectivity", "Information quality",
    "Integration", "D", "R", "V", "L", "DS", "PPN", "HMOS", "Orientation",
    "AI/automation used", "Human review", "Clear accountability", "Output validation"
])
writer.writerow([
    datetime.now().isoformat(timespec="seconds"),
    assessment_name, scope, project_stage, project_value, task, benchmark_name,
    I, C, device, connectivity, info_quality, integration, f"{D:.3f}",
    R, V, L, f"{DS:.3f}", f"{PPN:.3f}", f"{HMOS:.3f}", orientation,
    ai_used,
    human_review if ai_used else "N/A",
    accountability if ai_used else "N/A",
    validation if ai_used else "N/A",
])

safe_name = "".join(
    ch if ch.isalnum() or ch in ("-", "_") else "_"
    for ch in (assessment_name or "hmaf_assessment")
)

st.download_button(
    "Download assessment as CSV",
    data=output.getvalue(),
    file_name=f"{safe_name}_HMOS.csv",
    mime="text/csv",
    use_container_width=True,
)

with st.expander("Research basis and limitations"):
    st.markdown(
        """
**Research basis**

Digital tools showed their clearest comparative advantage for managing multiple projects. Management preference shifted with context: routine reporting and higher concurrent workload were more digitally oriented, while high-risk stages were more physically oriented. Physical presence was strongly supported for safety-critical judgement, inspections, verification and relational work. Digital-system reliability was positively associated with perceived digital effectiveness and remained independently associated in the exploratory regression. Human review, decision accountability and data validation were prioritised as safeguards for AI/advanced monitoring.

**Interpretive limits**

The HMAF/HMOS is a research-derived decision-support prototype, not a validated predictive equation. Equal weights are intentionally used for the six HMAF factors because the current study does not estimate defensible coefficients for all six factors. The exploratory regression coefficient for digital-system reliability is not used as an HMOS weight because that regression predicted perceived digital effectiveness, not the final digital/physical allocation score. PPN is an operational allocation index rather than a psychometric claim that risk, verification and relational leadership are one interchangeable construct. Strong physical-presence safeguards remain visible separately.

Do not interpret HMOS as a fixed percentage of onsite attendance. The research showed that onsite requirements are stage- and risk-responsive.
        """
    )

st.caption("HMAF / HMOS research prototype • Version 0.1")
