from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = (
    ROOT / "tests" / "extract" / "fixtures" / "extraction-boundary" / "contract"
)
SCHEMA_PATH = CONTRACT_ROOT / "evidence.schema.json"
VECTORS_PATH = CONTRACT_ROOT / "evidence.vectors.json"
SCHEMA_SHA256 = "587d018cb3c99b97439683ef7d6d2d55c984fb6c60509a236644454f475f62ea"
VECTORS_SHA256 = "c2e4eb3872c00e84190dce363eef5be0d456141e3b9528770a7ad3cab2b6e1b3"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def test_extraction_boundary_evidence_contract_vectors() -> None:
    assert _sha256(SCHEMA_PATH) == SCHEMA_SHA256
    assert _sha256(VECTORS_PATH) == VECTORS_SHA256
    schema = _read_json(SCHEMA_PATH)
    vectors = _read_json(VECTORS_PATH)
    assert schema["$id"].endswith("/extraction-boundary/evidence.schema.json")
    assert vectors["schema_version"] == "extraction_boundary_evidence_vectors_v1"

    for vector in vectors["valid"]:
        _validate_evidence(vector["value"])

    base = vectors["valid"][0]["value"]
    for vector in vectors["invalid"]:
        value = copy.deepcopy(base)
        if "remove" in vector:
            value.pop(vector["remove"])
        if "set" in vector:
            _set_path(value, vector["set"]["path"], vector["set"]["value"])
        try:
            _validate_evidence(value)
        except ValueError:
            continue
        raise AssertionError(f"invalid vector accepted: {vector['name']}")


def _validate_evidence(value: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "case_id",
        "surface",
        "run_id",
        "workflow_plan_nodes",
        "planned_executions",
        "boundary_events",
        "provider_bodies",
        "provider_executions",
        "not_applicable",
        "lineage",
        "candidate_review",
        "interactive_approval",
        "live_certification",
    }
    if set(value) != required:
        raise ValueError("unexpected evidence fields")
    if value["schema_version"] != "extraction_boundary_evidence_v1":
        raise ValueError("invalid schema version")
    if value["surface"] not in {
        "arcadia_legacy",
        "arcadia_v1",
        "generic_v1",
        "adp_v1",
        "current_repro",
    }:
        raise ValueError("invalid surface")
    if not value["boundary_events"]:
        raise ValueError("boundary events required")
    for event in value["boundary_events"]:
        if set(event) != {
            "event_id",
            "stage",
            "owner_repo",
            "owner_service",
            "entrypoint",
            "input_sha256",
            "output_sha256",
            "artifact_path",
        }:
            raise ValueError("invalid boundary event")
        _require_sha(event["input_sha256"])
        _require_sha(event["output_sha256"])
    for digest, body in value["provider_bodies"].items():
        _require_sha(digest)
        _require_sha(body["sha256"])
        if digest != body["sha256"]:
            raise ValueError("provider body key mismatch")
    for execution in value["provider_executions"]:
        attempts = execution["attempts"]
        if [attempt["attempt"] for attempt in attempts] != list(
            range(1, len(attempts) + 1)
        ):
            raise ValueError("provider attempts must be ordered within each execution")
    for item in value["lineage"]:
        kind = item.get("kind")
        if kind == "handoff":
            if set(item) != {"kind", "edge"}:
                raise ValueError("invalid handoff")
            _validate_edge(item["edge"])
        elif kind in {"fan_out", "fan_in"}:
            if set(item) != {"kind", "edges", "complete"}:
                raise ValueError("invalid fan lineage")
            if item["complete"] is not True or len(item["edges"]) < 2:
                raise ValueError("incomplete fan lineage")
            for edge in item["edges"]:
                _validate_edge(edge)
        elif kind == "terminal":
            if set(item) != {"kind", "event_id", "reason"}:
                raise ValueError("invalid terminal lineage")
            if item["reason"] not in {"success", "error"}:
                raise ValueError("invalid terminal reason")
        else:
            raise ValueError("invalid lineage kind")


def _validate_edge(edge: dict[str, Any]) -> None:
    if set(edge) != {"from_event_id", "to_event_id", "artifact_sha256"}:
        raise ValueError("invalid lineage edge")
    _require_sha(edge["artifact_sha256"])


def _require_sha(value: str) -> None:
    if not SHA256_RE.fullmatch(value):
        raise ValueError("invalid sha256")


def _set_path(root: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current: Any = root
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    last = parts[-1]
    if isinstance(current, list):
        current[int(last)] = value
    else:
        current[last] = value


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
