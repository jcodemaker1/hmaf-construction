def allocation_guidance(code):
    return {
        "physical":"The assessed conditions indicate that direct onsite management should form the primary allocation. Digital tools should support documentation, scheduling, traceability and information exchange rather than replace direct observation and leadership.",
        "hybrid_physical":"The assessed conditions indicate a hybrid model with greater emphasis on physical presence. Routine information processing can be managed digitally, while onsite involvement should be protected for verification, consequential decisions and human interaction.",
        "balanced":"The assessed conditions indicate a deliberately balanced hybrid allocation. Separate information-oriented work from safety-, verification- and relationship-dependent work, and adjust the balance as project conditions change.",
        "hybrid_digital":"The assessed conditions indicate a digitally leaning hybrid allocation. Use digital systems for routine coordination, reporting and information flow, while retaining targeted physical presence at high-value site moments.",
        "digital":"The assessed conditions indicate that a digital-first allocation may be appropriate for this activity, provided the digital environment remains reliable and no safety, verification, contractual or relational trigger requires physical presence.",
    }[code]

def management_plan(inputs, result, activity, ai_used, human_review, accountability, validation):
    digital=[]; onsite=[]; improve=[]
    reassess=["When the project moves into a different stage.","When the risk profile or consequence of decisions changes.",
              "When a hold point, inspection or irreversible work activity is reached.",
              "When concurrent workload or portfolio responsibilities materially change.",
              "When digital-system reliability materially improves or deteriorates."]
    if inputs["I"] >= 3:
        digital += ["Use digital systems for appropriate document control, information distribution and traceable communication.",
                    "Use current project information for routine reporting, programme review and coordination where direct observation is not required."]
    if inputs["C"] >= 4:
        digital.append("Use standardised digital reporting, dashboards and clear site-delegate/escalation arrangements to maintain management reach across projects or locations.")
    if inputs["R"] >= 4: onsite.append("Retain a competent onsite decision-maker and escalation path for high-consequence activities.")
    if inputs["V"] >= 4: onsite.append("Schedule direct inspection or physical verification before relevant hold points or irreversible work proceeds.")
    if inputs["L"] >= 4: onsite.append("Use face-to-face engagement for trust-building, mentoring, conflict resolution, difficult conversations or sensitive stakeholder interactions.")
    if activity == "Safety walk / high-risk work supervision": onsite.append("Retain competent physical presence for safety walks and high-risk work supervision.")
    elif activity == "Critical inspection / hold point": onsite.append("Retain competent physical presence for the critical inspection / hold point.")
    elif activity in ("Quality / rework inspection","Client / stakeholder walk-through"): onsite.append(f"Retain direct site involvement for the selected activity: {activity}.")
    readiness={"Suitable devices / access":inputs["devices"],"Site connectivity":inputs["connectivity"],
               "Information quality / currency":inputs["information_quality"],"System integration":inputs["integration"]}
    actions={"Suitable devices / access":"Improve access to suitable devices and permissions before increasing digital reliance.",
             "Site connectivity":"Improve site connectivity or establish a dependable offline/synchronisation process.",
             "Information quality / currency":"Strengthen information ownership, update frequency and quality control before increasing digital reliance.",
             "System integration":"Reduce duplicated systems/manual re-entry and improve interoperability or the single-source-of-truth process."}
    for name,score in readiness.items():
        if score < 3: improve.append(actions[name])
    if ai_used:
        if not human_review: improve.append("Introduce mandatory human review before consequential action is taken from AI or automated outputs.")
        if not accountability: improve.append("Assign clear accountability for final decisions informed by AI or automated outputs.")
        if not validation: improve.append("Implement validation of source data and automated outputs.")
    if not digital: digital.append("Use digital tools selectively for documentation, traceability and information exchange where appropriate.")
    if not onsite: onsite.append("Maintain an escalation pathway to physical verification if site conditions, consequence or stakeholder sensitivity increases.")
    if not improve: improve.append("No immediate readiness correction is indicated by the selected scores; continue monitoring the management environment.")
    return {"digital":digital,"onsite":onsite,"improve":improve,"reassess":reassess}
