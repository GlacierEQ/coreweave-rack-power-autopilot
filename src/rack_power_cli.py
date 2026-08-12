from __future__ import annotations

import argparse
import json
from pathlib import Path

from rack_power_autopilot import Decision, RackPowerAutopilot, RackPowerAutopilotRequest


def demo_payload() -> dict:
    return {
        "telemetry": {"rack_limit_kw": 100.0, "current_kw": 60.0, "max_temp_c": 72.0, "thermal_limit_c": 85.0, "ecc_error_rate": 0.0, "failed_gpu_fraction": 0.0, "telemetry_age_s": 2.0, "max_telemetry_age_s": 30.0},
        "jobs": [
            {"job_id": "urgent", "estimated_kw": 22.0, "priority": 10, "checkpointable": True, "preemptible": True, "min_power_fraction": 0.7},
            {"job_id": "batch", "estimated_kw": 16.0, "priority": 4, "checkpointable": True, "preemptible": True, "min_power_fraction": 0.6},
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute safe rack-power job admissions")
    parser.add_argument("--input", type=Path, help="JSON payload; defaults to a deterministic demo")
    parser.add_argument("--subject", default="rack-power-demo")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text()) if args.input else demo_payload()
    receipt = RackPowerAutopilot().evaluate(RackPowerAutopilotRequest(args.subject, payload, 1.0))
    print(json.dumps(receipt.as_dict(), indent=2, sort_keys=True))
    return 0 if receipt.decision is Decision.ALLOW else 2


if __name__ == "__main__":
    raise SystemExit(main())
