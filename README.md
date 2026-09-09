# Hybrid Management Allocation Framework (HMAF)

Research-derived Streamlit decision-support prototype for construction project management.

## What the tool does

The application calculates a Hybrid Management Orientation Score (HMOS) from:
- Information suitability (I)
- Concurrency/scalability requirement (C)
- Digital-system reliability (D)
- Risk/consequence (R)
- Verification/site-context requirement (V)
- Leadership/relational requirement (L)

Digital-system reliability is itself calculated from device access, site connectivity, information quality/currency, and system integration.

## Core equations

DS = (I + C + D) / 3

D = (Devices + Connectivity + Information Quality + Integration) / 4

PPN = (R + V + L) / 3

HMOS = 3 + (DS - PPN) / 2

## Important

This is a research-derived decision-support prototype, not a validated predictive equation and not a replacement for legal, contractual, WHS, inspection or professional obligations.

Before public release, confirm naming, attribution, intellectual-property and licensing arrangements with the research supervisor / university as appropriate.
