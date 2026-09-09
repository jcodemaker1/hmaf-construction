# HMAF Version 0.02
Hybrid Management Allocation Framework (HMAF) / Hybrid Management Orientation Score (HMOS).

## Version 0.02 changes
- No result before deliberate submission.
- Automatic research benchmarks from factual context inputs.
- Concurrent-project workload added.
- Industry-facing slider questions while academic variable codes remain visible.
- Digital readiness diagnostic.
- Physical-presence and AI governance safeguards.
- Management Allocation Plan.
- Evidence behind the recommendation.
- One-step sensitivity analysis.
- PDF assessment report and raw CSV.
- Assessment reference and model version.
- Automated calculation and threshold tests.

## Core formula
D = (Devices + Connectivity + Information Quality + Integration) / 4
DS = (I + C + D) / 3
PPN = (R + V + L) / 3
HMOS = 3 + (DS - PPN) / 2

## Run tests
python -m unittest discover -s tests -v
