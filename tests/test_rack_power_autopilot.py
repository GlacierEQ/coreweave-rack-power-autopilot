from __future__ import annotations

from rack_power_autopilot import Decision, RackPowerAutopilot, RackPowerAutopilotRequest


def telemetry(**overrides):
    base = {"rack_limit_kw": 100.0, "current_kw": 60.0, "max_temp_c": 70.0, "thermal_limit_c": 85.0, "ecc_error_rate": 0.0, "failed_gpu_fraction": 0.0, "telemetry_age_s": 2.0, "max_telemetry_age_s": 30.0}
    base.update(overrides)
    return base


def job(job_id: str, kw: float, *, priority: int = 1, checkpointable: bool = False, preemptible: bool = False, min_fraction: float = 0.6):
    return {"job_id": job_id, "estimated_kw": kw, "priority": priority, "checkpointable": checkpointable, "preemptible": preemptible, "min_power_fraction": min_fraction}


def evaluate(jobs, t=None):
    return RackPowerAutopilot().evaluate(RackPowerAutopilotRequest("rack-a", {"telemetry": t or telemetry(), "jobs": jobs}, 1.0))


def test_admits_jobs_within_safe_power_headroom() -> None:
    receipt = evaluate([job("a", 20, priority=5), job("b", 15, priority=2)])
    assert receipt.decision is Decision.ALLOW
    assert [row["job_id"] for row in receipt.metrics["admitted"]] == ["a", "b"]
    assert receipt.metrics["remaining_safe_kw"] == 5.0


def test_priority_orders_contention_deterministically() -> None:
    receipt = evaluate([job("low", 30, priority=1), job("high", 30, priority=9)])
    assert receipt.decision is Decision.ALLOW
    assert receipt.metrics["admitted"][0]["job_id"] == "high"
    assert receipt.metrics["rejected"][0]["job_id"] == "low"


def test_thermal_headroom_derates_rack_before_admission() -> None:
    receipt = evaluate([job("big", 35), job("small", 8, priority=2)], telemetry(max_temp_c=82.0))
    assert receipt.metrics["derate_factor"] == 0.7
    assert "thermal_derate" in receipt.metrics["derate_reasons"]
    assert receipt.metrics["admitted"][0]["job_id"] == "small"


def test_stale_telemetry_refuses_all_new_work() -> None:
    receipt = evaluate([job("a", 10)], telemetry(telemetry_age_s=60.0))
    assert receipt.decision is Decision.REFUSE
    assert receipt.metrics["rejected"][0]["reason"] == "telemetry_stale"


def test_critical_hardware_failure_fraction_refuses_admission() -> None:
    receipt = evaluate([job("a", 10)], telemetry(failed_gpu_fraction=0.30))
    assert receipt.decision is Decision.REFUSE
    assert receipt.metrics["rejected"][0]["reason"] == "hardware_failure_fraction_critical"


def test_checkpointable_preemptible_job_can_run_derated() -> None:
    receipt = evaluate([job("elastic", 50, checkpointable=True, preemptible=True, min_fraction=0.7)])
    assert receipt.decision is Decision.ALLOW
    row = receipt.metrics["admitted"][0]
    assert row["job_id"] == "elastic"
    assert row["derated"] is True
    assert row["power_fraction"] == 0.8


def test_noncheckpointable_job_is_not_partially_admitted() -> None:
    receipt = evaluate([job("rigid", 50)])
    assert receipt.decision is Decision.REFUSE
    assert receipt.metrics["rejected"][0]["reason"] == "insufficient_safe_power_headroom"


def test_existing_overlimit_rack_fails_closed() -> None:
    receipt = evaluate([job("a", 1)], telemetry(current_kw=101.0))
    assert receipt.decision is Decision.REFUSE
    assert "rack_already_over_power_limit" in receipt.reasons
