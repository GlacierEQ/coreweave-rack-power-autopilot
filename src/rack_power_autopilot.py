"""Rack Power Autopilot.

Turns rack power/thermal/reliability telemetry into deterministic job admission
and derating decisions. Safety margins are explicit; degraded telemetry never
silently increases admitted load.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class Decision(str, Enum):
    ALLOW = "ALLOW"
    REFUSE = "REFUSE"


@dataclass(frozen=True)
class RackPowerAutopilotRequest:
    subject_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    budget: float = 1.0
    grant_id: str | None = None
    not_after: float | None = None


@dataclass(frozen=True)
class RackPowerAutopilotReceipt:
    decision: Decision
    reasons: tuple[str, ...]
    digest: str
    metrics: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"decision": self.decision.value, "reasons": list(self.reasons), "digest": self.digest, "metrics": self.metrics}


class RackPowerError(ValueError):
    pass


class RackPowerAutopilot:
    MIN_BUDGET = 0.0

    @staticmethod
    def _num(value: Any, label: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RackPowerError(f"{label}_invalid")
        value = float(value)
        if not math.isfinite(value):
            raise RackPowerError(f"{label}_not_finite")
        if minimum is not None and value < minimum:
            raise RackPowerError(f"{label}_below_minimum")
        if maximum is not None and value > maximum:
            raise RackPowerError(f"{label}_above_maximum")
        return value

    @classmethod
    def _telemetry(cls, raw: Any) -> dict[str, float]:
        if not isinstance(raw, dict):
            raise RackPowerError("telemetry_missing")
        return {
            "rack_limit_kw": cls._num(raw.get("rack_limit_kw"), "rack_limit_kw", minimum=0.001),
            "current_kw": cls._num(raw.get("current_kw"), "current_kw", minimum=0),
            "max_temp_c": cls._num(raw.get("max_temp_c"), "max_temp_c", minimum=-50),
            "thermal_limit_c": cls._num(raw.get("thermal_limit_c"), "thermal_limit_c", minimum=-50),
            "ecc_error_rate": cls._num(raw.get("ecc_error_rate", 0.0), "ecc_error_rate", minimum=0),
            "failed_gpu_fraction": cls._num(raw.get("failed_gpu_fraction", 0.0), "failed_gpu_fraction", minimum=0, maximum=1),
            "telemetry_age_s": cls._num(raw.get("telemetry_age_s"), "telemetry_age_s", minimum=0),
            "max_telemetry_age_s": cls._num(raw.get("max_telemetry_age_s", 30.0), "max_telemetry_age_s", minimum=0.001),
        }

    @classmethod
    def _job(cls, raw: Any, index: int) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise RackPowerError(f"job_{index}_not_object")
        job_id = str(raw.get("job_id", "")).strip()
        if not job_id:
            raise RackPowerError(f"job_{index}_id_missing")
        priority = int(cls._num(raw.get("priority", 0), f"job_{index}_priority", minimum=0))
        return {
            "job_id": job_id,
            "estimated_kw": cls._num(raw.get("estimated_kw"), f"job_{index}_estimated_kw", minimum=0.001),
            "priority": priority,
            "checkpointable": bool(raw.get("checkpointable", False)),
            "preemptible": bool(raw.get("preemptible", False)),
            "min_power_fraction": cls._num(raw.get("min_power_fraction", 0.6), f"job_{index}_min_power_fraction", minimum=0, maximum=1),
        }

    @staticmethod
    def _derate(telemetry: dict[str, float]) -> tuple[float, list[str]]:
        reasons: list[str] = []
        factor = 1.0
        thermal_headroom = telemetry["thermal_limit_c"] - telemetry["max_temp_c"]
        if telemetry["telemetry_age_s"] > telemetry["max_telemetry_age_s"]:
            return 0.0, ["telemetry_stale"]
        if thermal_headroom <= 0:
            return 0.0, ["thermal_limit_reached"]
        if thermal_headroom < 5:
            factor = min(factor, 0.70)
            reasons.append("thermal_derate")
        if telemetry["failed_gpu_fraction"] >= 0.25:
            return 0.0, ["hardware_failure_fraction_critical"]
        if telemetry["failed_gpu_fraction"] > 0:
            factor = min(factor, max(0.5, 1.0 - telemetry["failed_gpu_fraction"] * 2))
            reasons.append("hardware_failure_derate")
        if telemetry["ecc_error_rate"] > 0.01:
            factor = min(factor, 0.75)
            reasons.append("ecc_derate")
        return factor, reasons

    def evaluate(self, req: RackPowerAutopilotRequest) -> RackPowerAutopilotReceipt:
        reasons: list[str] = []
        if not str(req.subject_id or "").strip():
            reasons.append("subject_id_missing")
        if isinstance(req.budget, bool) or not isinstance(req.budget, (int, float)) or not math.isfinite(float(req.budget)) or float(req.budget) <= self.MIN_BUDGET:
            reasons.append("budget_non_positive_or_invalid")
        payload = req.payload if isinstance(req.payload, dict) else {}
        if not isinstance(req.payload, dict):
            reasons.append("payload_not_object")
        admitted: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        factor = 0.0
        available_kw = 0.0
        derate_reasons: list[str] = []
        try:
            telemetry = self._telemetry(payload.get("telemetry"))
            if telemetry["current_kw"] > telemetry["rack_limit_kw"]:
                raise RackPowerError("rack_already_over_power_limit")
            factor, derate_reasons = self._derate(telemetry)
            safe_limit = telemetry["rack_limit_kw"] * factor
            available_kw = max(0.0, safe_limit - telemetry["current_kw"])
            raw_jobs = payload.get("jobs")
            if not isinstance(raw_jobs, list) or not raw_jobs:
                raise RackPowerError("jobs_missing")
            jobs = [self._job(row, i) for i, row in enumerate(raw_jobs)]
            if len({j["job_id"] for j in jobs}) != len(jobs):
                raise RackPowerError("duplicate_job_id")
            jobs.sort(key=lambda j: (-j["priority"], not j["checkpointable"], j["estimated_kw"], j["job_id"]))
            for job in jobs:
                if factor == 0:
                    rejected.append({"job_id": job["job_id"], "reason": derate_reasons[0] if derate_reasons else "rack_unavailable"})
                    continue
                required = job["estimated_kw"]
                if required <= available_kw:
                    admitted.append({"job_id": job["job_id"], "allocated_kw": required, "power_fraction": 1.0})
                    available_kw -= required
                    continue
                if job["checkpointable"] and job["preemptible"] and available_kw > 0:
                    fraction = available_kw / required
                    if fraction >= job["min_power_fraction"]:
                        admitted.append({"job_id": job["job_id"], "allocated_kw": round(available_kw, 9), "power_fraction": round(fraction, 9), "derated": True})
                        available_kw = 0.0
                        continue
                rejected.append({"job_id": job["job_id"], "reason": "insufficient_safe_power_headroom"})
        except RackPowerError as exc:
            reasons.append(str(exc))
        if not admitted and not reasons:
            reasons.append("no_job_admitted")
        decision = Decision.ALLOW if admitted and not reasons else Decision.REFUSE
        metrics = {
            "derate_factor": factor,
            "derate_reasons": derate_reasons,
            "admitted": admitted,
            "rejected": rejected,
            "remaining_safe_kw": round(available_kw, 9),
        }
        body = {"subject_id": req.subject_id, "decision": decision.value, "reasons": reasons, "metrics": metrics}
        return RackPowerAutopilotReceipt(decision, tuple(reasons or ["rack_power_admission_computed"]), _digest(body), metrics)


Mechanism = RackPowerAutopilot
