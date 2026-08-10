# Rack Power Autopilot

Independent GlacierEQ portfolio exhibit aligned to **CoreWeave** operating themes.

> **Not affiliated.** This repository is not affiliated with, endorsed by, employed by, or deployed at CoreWeave.
> No proprietary access, production deployment, customer impact, or company partnership is claimed.

## Bottleneck (GlacierEQ hypothesis)

Power, hardware reliability, scheduling, checkpointing, recovery, and utilization at cluster scale.

**Brick wall:** Maintaining economic and operational reliability amid component failures and huge infrastructure expansion.

**Observed public pressure (snapshot hypothesis):** AI clouds must operate mega-clusters across training, inference, observability, and rapidly expanding data-center capacity.

## Innovation mechanism

**Rack Power Autopilot** — Close the loop from power/thermal telemetry to job admission decisions with hard refuse states.

## Target roles

- Applied AI Systems Architect
- Forward-Deployed Engineer
- AI Infrastructure / Governance Engineer

## Application move

Build a failure-and-recovery topology case study around the GPU health system.

## Current scaffold state

This leaf is a **scaffold**: contracts, tests, and a stub mechanism exist so another engineer/AI can fill production-grade code without inventing company affiliation.

| Surface | Path |
|---------|------|
| Mechanism stub | `src/rack_power_autopilot.py` |
| Operate entry | `scripts/operate.py` |
| Contract tests | `tests/` |
| Target contract | `machine/target-contract.json` |
| **AI fill-in brief** | **`DEV_UP_INSTRUCTIONS.md`** |
| Issue contract | `ISSUE_CONTRACT.md` |

## Non-claims

- No CoreWeave employment, endorsement, proprietary data, or production use
- No customer, revenue, latency, or scale claims without separate receipts
- Scaffold tests define **intended behavior**, not verified production excellence

## Next gate

Create a simulated cluster failure benchmark with clearly bounded claims.
