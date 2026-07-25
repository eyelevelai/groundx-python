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
VECTORS_SHA256 = "bb05cd0e224f26ea40b3b956c8ee4291c6c94092c823ff4604d433131d8d0e71"
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
    _validate_semantics(value)


def _validate_semantics(value: dict[str, Any]) -> None:
    node_stages: dict[str, str] = {}
    for node in value["workflow_plan_nodes"]:
        node_id = node["node_id"]
        if node_id in node_stages:
            raise ValueError("workflow plan node IDs must be unique")
        node_stages[node_id] = node["stage"]

    not_applicable_stages = {
        item["stage"] for item in value["not_applicable"]
    }
    planned_by_id: dict[str, dict[str, Any]] = {}
    planned_nodes: set[str] = set()
    for execution in value["planned_executions"]:
        execution_id = execution["execution_id"]
        node_id = execution["node_id"]
        if execution_id in planned_by_id:
            raise ValueError("planned execution IDs must be unique")
        if node_id not in node_stages:
            raise ValueError("planned execution references unknown workflow node")
        planned_by_id[execution_id] = execution
        planned_nodes.add(node_id)
    for node_id, stage in node_stages.items():
        if node_id not in planned_nodes and stage not in not_applicable_stages:
            raise ValueError(
                "workflow plan node has no planned execution or not_applicable proof"
            )

    provider_bodies = value["provider_bodies"]
    provider_execution_ids: set[str] = set()
    for execution in value["provider_executions"]:
        execution_id = execution["execution_id"]
        planned = planned_by_id.get(execution_id)
        if planned is None:
            raise ValueError("provider execution must reference a planned execution")
        if execution_id in provider_execution_ids:
            raise ValueError("provider execution IDs must be unique")
        provider_execution_ids.add(execution_id)
        if execution["stage"] != node_stages[planned["node_id"]]:
            raise ValueError("provider execution stage does not match workflow node")
        for attempt in execution["attempts"]:
            if attempt["request_body_sha256"] not in provider_bodies:
                raise ValueError(
                    "provider attempt request body is missing from provider_bodies"
                )

    events: dict[str, dict[str, Any]] = {}
    for event in value["boundary_events"]:
        event_id = event["event_id"]
        if event_id in events:
            raise ValueError("boundary event IDs must be unique")
        events[event_id] = event
    outgoing: set[str] = set()
    terminal: set[str] = set()

    def validate_edge(edge: dict[str, Any]) -> None:
        from_id = edge["from_event_id"]
        to_id = edge["to_event_id"]
        if from_id not in events or to_id not in events:
            raise ValueError("lineage edge references unknown boundary event")
        artifact_sha = edge["artifact_sha256"]
        if (
            events[from_id]["output_sha256"] != artifact_sha
            or events[to_id]["input_sha256"] != artifact_sha
        ):
            raise ValueError(
                "lineage edge hash must match producer output and consumer input"
            )
        outgoing.add(from_id)

    for item in value["lineage"]:
        if item["kind"] == "handoff":
            validate_edge(item["edge"])
        elif item["kind"] in {"fan_out", "fan_in"}:
            for edge in item["edges"]:
                validate_edge(edge)
        elif item["kind"] == "terminal":
            event_id = item["event_id"]
            if event_id not in events:
                raise ValueError("terminal lineage references unknown boundary event")
            terminal.add(event_id)
    for event_id in events:
        if event_id in terminal and event_id in outgoing:
            raise ValueError("terminal boundary event cannot have a successor")
        if event_id not in terminal and event_id not in outgoing:
            raise ValueError("nonterminal boundary event must have a successor")

    review = value["candidate_review"]
    approval = value["interactive_approval"]
    if review["status"] == "approved" and approval is None:
        raise ValueError("approved candidate requires interactive approval")
    if approval is not None and (
        review["status"] != "approved"
        or approval["approved_sha256"] != review["candidate_sha256"]
    ):
        raise ValueError("interactive approval must match an approved candidate")


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
