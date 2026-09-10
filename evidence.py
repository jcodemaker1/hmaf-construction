# Research-derived evidence used by HMAF Version 0.06.
# Values below are descriptive study results, not population estimates.

SCENARIO_BENCHMARKS = {
    "routine": {
        "label": "Routine reporting / coordination",
        "mean": 3.70,
        "hybrid": 70.0,
        "evidence": "Routine reporting/coordination was the most digitally oriented project situation in the study.",
    },
    "multi": {
        "label": "Managing four or more projects",
        "mean": 3.60,
        "hybrid": 86.7,
        "evidence": "Management of four or more projects was relatively digitally oriented.",
    },
    "mid": {
        "label": "Mid-scale project ($5m–$50m)",
        "mean": 2.89,
        "hybrid": 82.1,
        "evidence": "Mid-scale projects were centred close to balanced hybrid management.",
    },
    "highrisk": {
        "label": "High-risk works / critical stage",
        "mean": 2.40,
        "hybrid": 63.3,
        "evidence": "High-risk works and critical stages were more physically oriented.",
    },
    "small": {
        "label": "Small project (<$5m)",
        "mean": 2.33,
        "hybrid": 78.8,
        "evidence": "Small projects were more physically oriented in the study sample.",
    },
}

# The study coded concurrent project load in the same natural 1–5 sequence.
PROJECT_COUNT_SCORE = {
    "1": 1.0,
    "2–3": 2.0,
    "4–5": 3.0,
    "6–8": 4.0,
    "9+": 5.0,
}

TASK_PRESENCE_EVIDENCE = {
    "Routine reporting / document coordination": None,
    "Safety walk / high-risk work supervision": 100.0,
    "Critical inspection / hold point": 93.8,
    "Quality / rework inspection": 87.5,
    "Client / stakeholder walk-through": 84.4,
    "Difficult conversation": 75.0,
    "Mentoring / coaching workers or supervisors": 71.9,
    "Conflict resolution": 68.8,
    "Complex trade coordination": 68.8,
    "Reading site conditions before a decision": 68.8,
    "Programme / scheduling review": None,
    "Design / document coordination": None,
    "Stakeholder coordination meeting": None,
    "Other / custom activity": None,
}

TASK_DIGITAL_EFFECTIVENESS = {
    "Quality / rework inspection": {
        "closest_measured_task": "Quality management and rework prevention",
        "mean": 3.12,
        "note": "Digital tools were approximately level with physical presence for the broader quality/rework management task.",
    },
    "Complex trade coordination": {
        "closest_measured_task": "Communication and coordination across trades",
        "mean": 3.42,
        "note": "Digital tools ranked relatively highly for cross-trade communication/coordination, but the adjusted midpoint test was not significant.",
    },
    "Stakeholder coordination meeting": {
        "closest_measured_task": "Stakeholder engagement",
        "mean": 3.55,
        "note": "Digital tools ranked relatively highly for stakeholder engagement, but the adjusted midpoint test was not significant.",
    },
    "Safety walk / high-risk work supervision": {
        "closest_measured_task": "Safety monitoring and situational awareness",
        "mean": 2.94,
        "note": "Digital tools were approximately level with physical presence for the broader safety-monitoring item, while Q12 strongly retained physical presence for safety walks/high-risk supervision.",
    },
}

RESEARCH_FACTS = {
    "safety_rII": 0.925,
    "trust_rII": 0.919,
    "communication_gap_rII": 0.832,
    "digital_visibility_rII": 0.788,
    "hybrid_rII": 0.788,
    "project_load_site_time_rs": -0.672,
    "project_load_group_q": 0.020,
    "project_load_group_effect": 0.758,
    "one_to_three_median_site_code": 5,
    "four_plus_median_site_code": 2,
    "digital_reliability_effectiveness_rs": 0.581,
    "digital_reliability_regression_B": 0.564,
    "digital_reliability_regression_beta": 0.559,
    "digital_reliability_regression_p": 0.004,
    "mid_at_least_31_pct": 46.9,
    "mid_stage_dependent_pct": 25.0,
}


def matched_context_anchors(project_value, concurrent_projects, activity, high_risk_critical_stage):
    """Return only directly matched Q11 scenario means used for contextual calibration."""
    anchors = []

    if project_value == "<$5m":
        anchors.append(SCENARIO_BENCHMARKS["small"])
    elif project_value == "$5m–$50m":
        anchors.append(SCENARIO_BENCHMARKS["mid"])

    if concurrent_projects in ("4–5", "6–8", "9+"):
        anchors.append(SCENARIO_BENCHMARKS["multi"])

    if activity == "Routine reporting / document coordination":
        anchors.append(SCENARIO_BENCHMARKS["routine"])

    if activity == "Safety walk / high-risk work supervision" or high_risk_critical_stage:
        anchors.append(SCENARIO_BENCHMARKS["highrisk"])

    seen = set()
    unique = []
    for item in anchors:
        if item["label"] not in seen:
            seen.add(item["label"])
            unique.append(item)
    return unique


def task_presence_cap(activity):
    """
    Operational safeguard from Q12.
    >=90%: final HMOS cannot exceed 2.84 (must remain physical-leaning or more physical).
    60–89.9%: final HMOS cannot exceed 3.15 (cannot become digital-leaning).
    These are transparent prototype decision rules, not estimated coefficients.
    """
    pct = TASK_PRESENCE_EVIDENCE.get(activity)
    if pct is None:
        return None
    if pct >= 90:
        return 2.84
    if pct >= 60:
        return 3.15
    return None


def workload_message(concurrent_projects):
    if concurrent_projects in ("4–5", "6–8", "9+"):
        return (
            "You selected four or more concurrent projects. In the study, respondents managing four or more projects "
            "reported substantially lower onsite-time rankings than those managing one to three projects. "
            "The 4+ project scenario had a mean management orientation of 3.60/5 and 86.7% selected a hybrid category."
        )
    if concurrent_projects in ("1", "2–3"):
        return (
            "You selected one to three concurrent projects. In the study, the one-to-three-project group reported "
            "substantially higher onsite-time rankings than the four-or-more group. The difference remained significant "
            "after multiple-testing correction (BH q = 0.020; rank-biserial r = 0.758)."
        )
    return None


def project_value_message(project_value):
    if project_value == "<$5m":
        b = SCENARIO_BENCHMARKS["small"]
        return (
            f"You selected a small project (<$5m). In the study, this situation had a mean orientation of "
            f"{b['mean']:.2f}/5 and {b['hybrid']:.1f}% selected a hybrid category; the overall direction was more physical."
        )
    if project_value == "$5m–$50m":
        b = SCENARIO_BENCHMARKS["mid"]
        return (
            f"You selected a mid-scale project ($5m–$50m). The study mean was {b['mean']:.2f}/5 and "
            f"{b['hybrid']:.1f}% selected a hybrid category. Separately, 46.9% nominated at least 31% onsite attendance "
            f"and 25.0% said one fixed percentage was inappropriate because requirements depended on project stage."
        )
    if project_value in ("$50m–$250m", ">$250m"):
        return (
            "The study recorded this project-value band as respondent context, but Q11 did not provide a directly matched "
            "management-orientation scenario for projects above $50m. No project-value calibration is therefore applied."
        )
    return None


def activity_message(activity):
    pct = TASK_PRESENCE_EVIDENCE.get(activity)
    if pct is not None:
        return (
            f"For the selected activity, {pct:.1f}% of valid study respondents identified it as requiring physical presence. "
            "HMAF uses this as a task-specific physical-presence safeguard."
        )
    if activity == "Routine reporting / document coordination":
        b = SCENARIO_BENCHMARKS["routine"]
        return (
            f"Routine reporting/coordination was the most digitally oriented tested project situation, "
            f"with a mean orientation of {b['mean']:.2f}/5; {b['hybrid']:.1f}% selected a hybrid category."
        )
    return (
        "The selected activity did not have a directly matching physical-presence percentage in the study. "
        "No task-specific cap is applied; the factor assessment remains the primary basis for this activity."
    )


def stage_message(high_risk_critical_stage, project_stage):
    if high_risk_critical_stage:
        b = SCENARIO_BENCHMARKS["highrisk"]
        stage_label = project_stage.lower() if project_stage != "Not specified" else "project"
        return (
            f"You identified the current {stage_label} stage as high-risk or critical. The study's high-risk/critical-stage "
            f"scenario had a mean orientation of {b['mean']:.2f}/5 and was more physically oriented."
        )
    return (
        "The named construction stage is recorded for context, but the study did not estimate separate numerical weights "
        "for individual stages such as Structure, Envelope or Fit-out. It directly tested high-risk/critical stages, so no "
        "stage calibration is applied unless the assessor identifies the current stage as high-risk or critical."
    )
