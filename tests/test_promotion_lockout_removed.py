from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_secret_bound_promotion_artifacts_are_retired() -> None:
    retired = (
        ROOT / "src" / "promotion_authority.py",
        ROOT / "machine" / "promotion_authority.json",
        ROOT / "tests" / "test_promotion_authority.py",
        ROOT / "scripts" / "verify_promotion_grant.py",
    )
    assert all(not path.exists() for path in retired)


def test_keyless_current_state_preserves_non_deployment_boundary() -> None:
    proof = json.loads((ROOT / "machine" / "proof_receipt.json").read_text())
    state = json.loads((ROOT / "machine" / "excellence-state.json").read_text())
    contract = json.loads((ROOT / "machine" / "target-contract.json").read_text())

    assert proof["repository"] == "GlacierEQ/coreweave-rack-power-autopilot"
    assert state["principal_state"] == "FUNCTIONAL_CANDIDATE"
    assert state["promotion_authority"]["status"] == "RETIRED_KEYLESS"
    assert contract["current"]["state"] == "FUNCTIONAL_CANDIDATE"
    assert contract["current"]["deployed"] is False
