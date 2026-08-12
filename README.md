# Rack Power Autopilot

Independent GlacierEQ portfolio implementation aligned to **CoreWeave** operating themes.

> **Not affiliated.** This repository is not affiliated with, endorsed by, employed by, or deployed at CoreWeave. No proprietary access, production deployment, customer impact, or company partnership is claimed.

## Purpose

Turn power, thermal, hardware-reliability, and telemetry freshness signals into **hard job-admission decisions** instead of treating rack capacity as a static number.

## Implemented system

`RackPowerAutopilot` computes a safe rack envelope before admitting work:

- fails closed on stale telemetry or an already-overlimit rack;
- refuses admission at the thermal ceiling or critical failed-GPU fraction;
- derates available power as thermal headroom narrows, ECC errors rise, or hardware fails;
- sorts jobs deterministically by priority, checkpointability, power request, and id;
- fully admits jobs that fit the safe envelope;
- permits partial/derated admission only for checkpointable + preemptible jobs whose declared minimum power fraction remains satisfied;
- exposes rejected jobs and reason codes rather than silently oversubscribing.

The receipt reports derate factor, derate reasons, admitted allocations, rejected work, remaining safe kW, and a deterministic digest.

## Run

```bash
python -m pytest -q
python scripts/operate.py
```

Build and install:

```bash
python -m pip install build
python -m build
python -m pip install dist/*.whl
rack-power-autopilot
```

## Proof surface

- `src/rack_power_autopilot.py` — telemetry/derating/admission engine
- `src/rack_power_cli.py` — installable runtime
- `tests/test_rack_power_autopilot.py` — contention, thermal, stale telemetry, hardware failure and partial-admission behavior
- `tests/test_adversarial.py` — fail-closed adversarial coverage
- `.github/workflows/tests.yml` — tests + cold-start + wheel build/install + installed CLI
- `machine/` — existing Helix control-plane and promotion surfaces remain preserved

## Current boundary

This operates on supplied telemetry and job estimates. It does not control CoreWeave infrastructure or claim production-scale measurements. The next material depth step is a permitted simulator/telemetry adapter that feeds repeated rack observations through the same admission contract and measures recovery behavior under induced failures.
