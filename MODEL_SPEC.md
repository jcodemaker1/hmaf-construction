# HMAF / HMOS Model Specification — Version 0.05

## Purpose
Operationalise practitioner-grounded findings concerning allocation of digital and physical construction-management effort.

## Core constructs
Digital Suitability: I, C, D.
Physical Presence Need: R, V, L.

## Equations
D = (Devices + Connectivity + Information Quality + Integration) / 4
DS = (I + C + D) / 3
PPN = (R + V + L) / 3
HMOS = 3 + (DS - PPN) / 2

## Categories
HMOS < 1.5 — Mostly physical presence
1.5 <= HMOS < 2.5 — Hybrid leaning physical
2.5 <= HMOS < 3.5 — Balanced hybrid
3.5 <= HMOS < 4.5 — Hybrid leaning digital
HMOS >= 4.5 — Mostly digital tools

## Weighting
Equal weights are retained because the current research does not estimate validated coefficients for all six final allocation inputs. The exploratory regression coefficient for digital reliability predicted perceived digital effectiveness, not the final HMAF allocation outcome, so it is evidence supporting inclusion of D rather than a validated HMOS weight.

## Safeguards
Task-specific physical-presence evidence, high-consequence verification, low digital readiness, and AI human-review/accountability/validation controls remain separate from the aggregate HMOS.

## Stage responsiveness
HMOS should be recalculated when stage, task, risk, workload or digital readiness materially changes. It must not be converted directly to one fixed onsite-attendance percentage.


## Version 0.05 reporting and explainability
Version 0.05 does not alter the HMOS mathematics. It introduces a deliberate two-page assessment report:
- Page 1: assessment context, DS, PPN, HMOS, allocation guidance, management allocation plan and research benchmarks.
- Page 2: decision drivers, digital-environment reliability, AI/automated-monitoring governance, empirical evidence, sensitivity analysis and limitations.

Research benchmark differences are expressed directionally in management language rather than as an unexplained positive/negative number.
