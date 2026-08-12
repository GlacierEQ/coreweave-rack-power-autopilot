# DEV_UP_INSTRUCTIONS — implementation record

**Repository:** `GlacierEQ/coreweave-rack-power-autopilot`  
**Independent company lens:** CoreWeave  
**Innovation:** Rack Power Autopilot

## Mission

Close the loop from rack telemetry to safe job admission while preserving checkpoint/recovery semantics for elastic work.

## Implemented

The generic scaffold has been replaced by a telemetry-driven derating and admission controller.

`src/rack_power_autopilot.py` now:

- validates rack power, temperature, ECC, hardware-failure and telemetry-age evidence;
- fails closed on stale telemetry, thermal exhaustion and critical hardware failure;
- computes explicit thermal/ECC/hardware derating;
- orders jobs by priority and checkpointability;
- admits full-power jobs within safe headroom;
- permits bounded partial allocation only for checkpointable/preemptible jobs;
- exposes every rejection and remaining safe power in a deterministic receipt.

`src/rack_power_cli.py` and `scripts/operate.py` execute the mechanism directly. The project is packaged with the `rack-power-autopilot` console command.

## Verification contract

Behavioral tests cover safe admission, deterministic contention, thermal derating, stale telemetry, critical failure, elastic partial power, rigid-job refusal, and an already-overlimit rack. Existing adversarial coverage remains active.

CI must pass tests, cold-start, wheel build/install and installed CLI execution before Helix promotion evidence can be minted.

## Truth boundary

No CoreWeave affiliation, proprietary access, production deployment, customer impact, or company partnership is claimed. External telemetry/scheduler adapters remain a further end-to-end depth step.
