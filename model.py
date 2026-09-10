from dataclasses import dataclass
from statistics import mean
from typing import Dict, List, Optional, Tuple

MODEL_VERSION = "0.06"


@dataclass(frozen=True)
class HMAFResult:
    digital_reliability: float
    concurrency_score: float
    digital_suitability: float
    physical_presence_need: float
    base_hmos: float
    context_anchor: Optional[float]
    context_calibrated_hmos: float
    task_cap: Optional[float]
    hmos: float
    orientation: str
    orientation_code: str


def calculate_digital_reliability(devices, connectivity, information_quality, integration):
    return (devices + connectivity + information_quality + integration) / 4


def calculate_digital_suitability(information_suitability, concurrency_score, digital_reliability):
    return (information_suitability + concurrency_score + digital_reliability) / 3


def calculate_physical_presence_need(risk, verification, leadership):
    return (risk + verification + leadership) / 3


def classify_hmos(score: float) -> Tuple[str, str]:
    # V0.06 narrows the balanced band so directional lean is shown sooner.
    if score < 1.50:
        return "Mostly physical presence", "physical"
    if score < 2.85:
        return "Hybrid leaning physical", "hybrid_physical"
    if score <= 3.15:
        return "Balanced hybrid", "balanced"
    if score < 4.50:
        return "Hybrid leaning digital", "hybrid_digital"
    return "Mostly digital tools", "digital"


def calculate_hmaf(
    information_suitability,
    concurrency_score,
    devices,
    connectivity,
    information_quality,
    integration,
    risk,
    verification,
    leadership,
    context_means: Optional[List[float]] = None,
    task_cap: Optional[float] = None,
):
    d = calculate_digital_reliability(devices, connectivity, information_quality, integration)
    ds = calculate_digital_suitability(information_suitability, concurrency_score, d)
    ppn = calculate_physical_presence_need(risk, verification, leadership)

    base = 3 + ((ds - ppn) / 2)
    base = max(1.0, min(5.0, base))

    context_means = [float(x) for x in (context_means or [])]
    context_anchor = mean(context_means) if context_means else None

    if context_anchor is None:
        calibrated = base
    else:
        # Factor assessment retains twice the influence of directly matched Q11 context evidence.
        calibrated = ((2 * base) + context_anchor) / 3

    calibrated = max(1.0, min(5.0, calibrated))
    final = min(calibrated, task_cap) if task_cap is not None else calibrated
    final = max(1.0, min(5.0, final))
    orientation, code = classify_hmos(final)

    return HMAFResult(
        d, concurrency_score, ds, ppn, base, context_anchor,
        calibrated, task_cap, final, orientation, code
    )


def one_step_sensitivity(inputs: Dict[str, float], result: HMAFResult, context_means=None, task_cap=None):
    scenarios = []
    names = {"I": "Information suitability", "R": "Risk / consequence", "V": "Verification / site context", "L": "Leadership / relational requirement"}

    def recalc(changes):
        data = dict(inputs)
        data.update(changes)
        return calculate_hmaf(
            data["I"], data["C"], data["devices"], data["connectivity"],
            data["information_quality"], data["integration"], data["R"], data["V"], data["L"],
            context_means=context_means, task_cap=task_cap,
        )

    if inputs["I"] < 5:
        new = recalc({"I": inputs["I"] + 1})
        scenarios.append({"label": f"If Information suitability increased from {inputs['I']:.0f} to {inputs['I']+1:.0f}", "new_hmos": new.hmos, "new_orientation": new.orientation, "changed_category": new.orientation_code != result.orientation_code})

    for key in ("R", "V", "L"):
        if inputs[key] > 1:
            new = recalc({key: inputs[key] - 1})
            scenarios.append({"label": f"If {names[key]} reduced from {inputs[key]:.0f} to {inputs[key]-1:.0f}", "new_hmos": new.hmos, "new_orientation": new.orientation, "changed_category": new.orientation_code != result.orientation_code})

    readiness = {"devices": inputs["devices"], "connectivity": inputs["connectivity"], "information_quality": inputs["information_quality"], "integration": inputs["integration"]}
    weakest = min(readiness, key=readiness.get)
    readiness_names = {"devices": "device access", "connectivity": "site connectivity", "information_quality": "information quality", "integration": "system integration"}
    if readiness[weakest] < 5:
        new = recalc({weakest: readiness[weakest] + 1})
        scenarios.append({"label": f"If the weakest digital-readiness condition ({readiness_names[weakest]}) improved from {readiness[weakest]:.0f} to {readiness[weakest]+1:.0f}", "new_hmos": new.hmos, "new_orientation": new.orientation, "changed_category": new.orientation_code != result.orientation_code})

    scenarios.sort(key=lambda x: (not x["changed_category"], -abs(x["new_hmos"] - result.hmos)))
    return scenarios
