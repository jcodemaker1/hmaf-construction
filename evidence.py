SCENARIO_BENCHMARKS = {
    "routine":{"label":"Routine reporting / coordination","mean":3.70,"hybrid":70.0,"evidence":"Routine reporting/coordination was the most digitally oriented project situation in the study."},
    "multi":{"label":"Managing four or more projects","mean":3.60,"hybrid":86.7,"evidence":"Managing four or more projects was relatively digitally oriented and had the highest observed hybrid-category selection."},
    "mid":{"label":"Mid-scale project ($5m–$50m)","mean":2.89,"hybrid":82.1,"evidence":"Mid-scale projects were centred close to balanced hybrid management."},
    "highrisk":{"label":"High-risk works / critical stage","mean":2.40,"hybrid":63.3,"evidence":"High-risk works and critical stages were more physically oriented."},
    "small":{"label":"Small project (<$5m)","mean":2.33,"hybrid":78.8,"evidence":"Small projects were more physically oriented in the study sample."},
}
TASK_PRESENCE_EVIDENCE = {
    "Routine reporting / document coordination":None,
    "Safety walk / high-risk work supervision":100.0,
    "Critical inspection / hold point":93.8,
    "Quality / rework inspection":87.5,
    "Client / stakeholder walk-through":84.4,
    "Difficult conversation":75.0,
    "Mentoring / coaching workers or supervisors":71.9,
    "Conflict resolution":68.8,
    "Complex trade coordination":68.8,
    "Reading site conditions before a decision":68.8,
    "Programme / scheduling review":None,
    "Design / document coordination":None,
    "Stakeholder coordination meeting":None,
    "Other / custom activity":None,
}
RESEARCH_FACTS = {
    "safety_rII":0.925,"trust_rII":0.919,"communication_gap_rII":0.832,"digital_visibility_rII":0.788,
    "hybrid_rII":0.788,"project_load_site_time_rs":-0.672,"digital_reliability_effectiveness_rs":0.581,
    "digital_reliability_regression_B":0.564,"digital_reliability_regression_beta":0.559,
    "digital_reliability_regression_p":0.004,"mid_at_least_31_pct":46.9,"mid_stage_dependent_pct":25.0,
}
def automatic_benchmarks(project_value, concurrent_projects, activity):
    keys=[]
    if activity in ("Routine reporting / document coordination","Programme / scheduling review"): keys.append("routine")
    if concurrent_projects in ("4–5","6–8","9+"): keys.append("multi")
    if project_value == "$5m–$50m": keys.append("mid")
    elif project_value == "<$5m": keys.append("small")
    if activity in ("Safety walk / high-risk work supervision","Critical inspection / hold point"): keys.append("highrisk")
    out=[]
    for k in keys:
        if k not in out: out.append(k)
    return [SCENARIO_BENCHMARKS[k] for k in out]
