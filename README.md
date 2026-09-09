# HMAF Version 0.03
Hybrid Management Allocation Framework (HMAF) / Hybrid Management Orientation Score (HMOS).

## Version 0.03 changes
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


## Version 0.04 updates
- Removed stray list/null output artifacts from the app display.
- Updated PDF output to a green/teal palette.
- Added developer / research-paper footer line to PDF reports.
- Added metadata.py for easy editing of developer name and research paper title.


## Version 0.04 final refinements
- Renamed "Closest management activity" to "Management activity being assessed".
- Research benchmarks now use a compact card layout.
- Added a Reset assessment control.
- Tightened allocation-guidance wording.
- PDF hierarchy refined with a dedicated allocation-guidance panel.
- PDF uses a green/teal visual system throughout.
- PDF footer identifies developer, Deakin University and the research paper.
- Developer: Mr. Jarrad Kyne
- Research paper: The effectiveness of digital project management tools compared to physical site presence in construction
