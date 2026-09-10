# HMAF / HMOS Model Specification — Version 0.06

## Purpose
Version 0.06 integrates tutor review into the research-derived Hybrid Management Allocation Framework while retaining transparent separation between factor-based assessment, directly matched project-context evidence, and task-specific physical-presence safeguards.

## 1. Digital Environment Reliability
`D = (Devices + Connectivity + Information Quality + Integration) / 4`

## 2. Concurrent project load
Concurrent projects are no longer a separate subjective slider. C is derived from the same ordered workload categories used in the study:
- 1 project = 1
- 2–3 projects = 2
- 4–5 projects = 3
- 6–8 projects = 4
- 9+ projects = 5

This means project count directly changes Digital Suitability.

## 3. Digital Suitability
`DS = (I + C + D) / 3`

## 4. Physical Presence Need
`PPN = (R + V + L) / 3`

## 5. Factor-based HMOS
`Base HMOS = 3 + (DS - PPN) / 2`

## 6. Context Orientation Anchor (COA)
Only directly matched Q11 study situations are used:
- Routine reporting / coordination = 3.70
- Managing four or more projects = 3.60
- Mid-scale project ($5m–$50m) = 2.89
- High-risk works / critical stage = 2.40
- Small project (<$5m) = 2.33

Where multiple matched situations apply:
`COA = mean(applicable observed situation means)`

No project-value anchor is applied above $50m because the study did not contain a directly matched Q11 orientation scenario for those bands.

The named stage (e.g. Structure, Envelope or Fit-out) does not receive an invented numerical weight. A stage anchor is applied only when the assessor identifies the current stage as high-risk or critical, which directly matches Q11.

## 7. Context-calibrated HMOS
`Context-calibrated HMOS = (2 × Base HMOS + COA) / 3`

The factor assessment retains twice the influence of the matched research context. This is a transparent prototype calibration rule, not a statistically estimated coefficient.

If no COA is available, Context-calibrated HMOS = Base HMOS.

## 8. Task-specific physical-presence safeguard
Q12 found majority support for physical presence across several activities.

Prototype safeguard rules:
- Q12 physical-presence selection >= 90%: Final HMOS cannot exceed 2.84.
- Q12 physical-presence selection 60–89.9%: Final HMOS cannot exceed 3.15.
- No directly matched Q12 percentage: no task cap.

This prevents the aggregate result from becoming inconsistent with strong task-specific physical-presence evidence. These caps are operational prototype rules and require validation.

## 9. Final HMOS
`Final HMOS = min(Context-calibrated HMOS, applicable task safeguard cap)`

bounded to 1–5.

## 10. Revised orientation categories
Version 0.06 narrows Balanced Hybrid so directional lean appears sooner:
- 1.00–1.49: Mostly physical presence
- 1.50–2.84: Hybrid leaning physical
- 2.85–3.15: Balanced hybrid
- 3.16–4.49: Hybrid leaning digital
- 4.50–5.00: Mostly digital tools

These revised boundaries are prototype interpretation rules, not statistically estimated cut-points.

## 11. Research evidence display
The app shows plain-language research evidence for concurrent workload, project value, management activity, stage criticality, task-specific physical-presence requirements, digital readiness and AI governance.

The previous “Research benchmarks relevant to this assessment” section is removed and replaced by:
- “What the study says about your selected context”; and
- “How project context influenced the HMOS”.

## 12. Validation status
Version 0.06 remains research-derived and requires usability, face-validity and external validation before it should be described as a validated predictive tool.
