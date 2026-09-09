from dataclasses import dataclass
from typing import Dict, Tuple

MODEL_VERSION = "0.02"

@dataclass(frozen=True)
class HMAFResult:
    digital_reliability: float
    digital_suitability: float
    physical_presence_need: float
    hmos: float
    orientation: str
    orientation_code: str

def calculate_digital_reliability(devices: float, connectivity: float, information_quality: float, integration: float) -> float:
    return (devices + connectivity + information_quality + integration) / 4

def calculate_digital_suitability(information_suitability: float, concurrency: float, digital_reliability: float) -> float:
    return (information_suitability + concurrency + digital_reliability) / 3

def calculate_physical_presence_need(risk: float, verification: float, leadership: float) -> float:
    return (risk + verification + leadership) / 3

def classify_hmos(score: float) -> Tuple[str, str]:
    if score < 1.5:
        return "Mostly physical presence", "physical"
    if score < 2.5:
        return "Hybrid leaning physical", "hybrid_physical"
    if score < 3.5:
        return "Balanced hybrid", "balanced"
    if score < 4.5:
        return "Hybrid leaning digital", "hybrid_digital"
    return "Mostly digital tools", "digital"

def calculate_hmaf(information_suitability: float, concurrency: float, devices: float, connectivity: float,
                   information_quality: float, integration: float, risk: float, verification: float,
                   leadership: float) -> HMAFResult:
    d = calculate_digital_reliability(devices, connectivity, information_quality, integration)
    ds = calculate_digital_suitability(information_suitability, concurrency, d)
    ppn = calculate_physical_presence_need(risk, verification, leadership)
    hmos = max(1.0, min(5.0, 3 + ((ds - ppn) / 2)))
    orientation, code = classify_hmos(hmos)
    return HMAFResult(d, ds, ppn, hmos, orientation, code)

def one_step_sensitivity(inputs: Dict[str, float], result: HMAFResult):
    scenarios = []
    names = {"I":"Information suitability","C":"Concurrency / scalability","R":"Risk / consequence",
             "V":"Verification / site context","L":"Leadership / relational requirement"}
    def recalc(changes):
        data = dict(inputs); data.update(changes)
        return calculate_hmaf(data["I"], data["C"], data["devices"], data["connectivity"],
                              data["information_quality"], data["integration"], data["R"], data["V"], data["L"])
    for key in ("I","C"):
        if inputs[key] < 5:
            new = recalc({key: inputs[key] + 1})
            scenarios.append({"label":f"If {names[key]} increased from {inputs[key]:.0f} to {inputs[key]+1:.0f}",
                              "new_hmos":new.hmos,"new_orientation":new.orientation,
                              "changed_category":new.orientation_code != result.orientation_code})
    for key in ("R","V","L"):
        if inputs[key] > 1:
            new = recalc({key: inputs[key] - 1})
            scenarios.append({"label":f"If {names[key]} reduced from {inputs[key]:.0f} to {inputs[key]-1:.0f}",
                              "new_hmos":new.hmos,"new_orientation":new.orientation,
                              "changed_category":new.orientation_code != result.orientation_code})
    readiness = {"devices":inputs["devices"],"connectivity":inputs["connectivity"],
                 "information_quality":inputs["information_quality"],"integration":inputs["integration"]}
    weakest_key = min(readiness, key=readiness.get)
    readiness_names = {"devices":"device access","connectivity":"site connectivity",
                       "information_quality":"information quality","integration":"system integration"}
    if readiness[weakest_key] < 5:
        new = recalc({weakest_key: readiness[weakest_key] + 1})
        scenarios.append({"label":f"If the weakest readiness condition ({readiness_names[weakest_key]}) improved from {readiness[weakest_key]:.0f} to {readiness[weakest_key]+1:.0f}",
                          "new_hmos":new.hmos,"new_orientation":new.orientation,
                          "changed_category":new.orientation_code != result.orientation_code})
    scenarios.sort(key=lambda x: (not x["changed_category"], -abs(x["new_hmos"] - result.hmos)))
    return scenarios
