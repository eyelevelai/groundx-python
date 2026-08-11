from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import importlib.util
import json
import typing
from pathlib import Path

_PROJECTION_PATH = Path(__file__).resolve().parent / "fixtures" / "extraction-boundary" / "catalog.json"
_PROJECTION = json.loads(_PROJECTION_PATH.read_text())
SURFACES = tuple(case["surface"] for case in _PROJECTION["cases"])
_CASE_IDS = {case["surface"]: case["id"] for case in _PROJECTION["cases"]}
_XRAY_ARTIFACT = "internal_arcadia_load_xray_predecessor"
_HANDOFF_ARTIFACT = "internal_arcadia_download_workflow_load"
_COMPLETE_OUTPUT_ARTIFACT = "internal_arcadia_sdk_reassembly_output"
_COMPLETE_OUTPUT_MEMBERS = (
    "workflow_output",
    "relationship_output",
    "final_output",
    "diagnostics",
    "source_provenance",
)
_CAPTURE_IDENTITY_FIELDS = (
    "schema_version",
    "run_id",
    "surface",
    "case_id",
    "bucket_id",
    "workflow_id",
    "capture_config_hash",
)


def _read_json(path: Path) -> dict[str, typing.Any]:
    return typing.cast(dict[str, typing.Any], json.loads(path.read_text()))


def _write_json(path: Path, value: typing.Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_inside(root: Path, relative: str) -> Path:
    root = root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"candidate path escapes its root: {relative}") from error
    return path


def _changes(
    accepted: typing.Any,
    candidate: typing.Any,
    pointer: str = "",
) -> list[dict[str, typing.Any]]:
    if type(accepted) is not type(candidate):
        return [{"path": pointer or "/", "before": accepted, "after": candidate}]
    if isinstance(accepted, dict):
        result: list[dict[str, typing.Any]] = []
        for key in sorted(set(accepted) | set(candidate)):
            child = f"{pointer}/{key}"
            if key not in accepted:
                result.append({"path": child, "before": None, "after": candidate[key]})
            elif key not in candidate:
                result.append({"path": child, "before": accepted[key], "after": None})
            else:
                result.extend(_changes(accepted[key], candidate[key], child))
        return result
    if isinstance(accepted, list):
        if accepted == candidate:
            return []
        return [{"path": pointer or "/", "before": accepted, "after": candidate}]
    if accepted != candidate:
        return [{"path": pointer or "/", "before": accepted, "after": candidate}]
    return []


def _load_replay_module(repo_root: Path) -> typing.Any:
    path = repo_root / "tests" / "extract" / "test_extraction_boundary_reassembly.py"
    spec = importlib.util.spec_from_file_location("extraction_boundary_replay", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load boundary replay from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_replay_inputs_module(repo_root: Path) -> typing.Any:
    path = repo_root / "tests" / "extract" / "_boundary_replay_inputs.py"
    spec = importlib.util.spec_from_file_location("extraction_boundary_replay_inputs", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load boundary replay inputs from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _selected_surfaces(value: str | None) -> tuple[str, ...]:
    if value is None:
        return SURFACES
    selected = tuple(dict.fromkeys(item.strip() for item in value.split(",") if item.strip()))
    invalid = sorted(set(selected) - set(SURFACES))
    if invalid:
        raise ValueError(f"unsupported surfaces: {', '.join(invalid)}")
    if not selected:
        raise ValueError("at least one surface is required")
    return selected


def _required(
    value: dict[str, typing.Any],
    key: str,
    label: str,
) -> typing.Any:
    result = value.get(key)
    if result is None or result == "":
        raise ValueError(f"{label}.{key} is required")
    return result


def _required_mapping(
    value: dict[str, typing.Any],
    key: str,
    label: str,
) -> dict[str, typing.Any]:
    result = _required(value, key, label)
    if not isinstance(result, dict):
        raise ValueError(f"{label}.{key} is required")
    return result


def _validate_entry_provenance(
    *,
    entry: dict[str, typing.Any],
    manifest: dict[str, typing.Any],
    label: str,
) -> None:
    expected = {
        "source_run_id": _required(manifest, "run_id", "manifest"),
        "source_run_mode": _required(manifest, "run_mode", "manifest"),
        "source_boundary_manifest_sha256": _required(
            manifest,
            "source_boundary_manifest_sha256",
            "manifest",
        ),
    }
    for field, manifest_value in expected.items():
        entry_value = _required(entry, field, label)
        if entry_value != manifest_value:
            raise ValueError(f"{label} {field} does not match manifest")


def _capture_identity(
    handoff: dict[str, typing.Any],
    *,
    branch: str,
) -> dict[str, typing.Any]:
    branch_value = handoff.get(branch)
    if not isinstance(branch_value, dict):
        raise ValueError(f"handoff.{branch}.workflow_capture is required")
    return _required_mapping(branch_value, "workflow_capture", f"handoff.{branch}")


def _validate_candidate_pair(
    *,
    manifest: dict[str, typing.Any],
    surface: str,
    xray_entry: dict[str, typing.Any],
    xray_path: Path,
    handoff_entry: dict[str, typing.Any],
    handoff_path: Path,
) -> None:
    _validate_entry_provenance(
        entry=xray_entry,
        manifest=manifest,
        label="X-Ray predecessor candidate",
    )
    _validate_entry_provenance(
        entry=handoff_entry,
        manifest=manifest,
        label="producer handoff",
    )

    envelope = _read_json(xray_path)
    if _required(envelope, "kind", "envelope") != "xray_predecessor":
        raise ValueError("X-Ray predecessor kind is invalid")
    xray = _required_mapping(envelope, "value", "envelope")
    source = _required_mapping(envelope, "source", "envelope")
    if _required(source, "source_kind", "envelope.source") != "live_capture":
        raise ValueError("X-Ray predecessor is not a live capture")
    for field in ("run_id", "process_id", "document_id"):
        _required(source, field, "X-Ray predecessor source")
    encoded = _required(envelope, "raw_xray_model_base64", "envelope")
    digest = _required(envelope, "raw_xray_model_sha256", "envelope")
    byte_count = _required(envelope, "raw_xray_model_bytes", "envelope")
    if not isinstance(encoded, str) or not isinstance(digest, str):
        raise ValueError("X-Ray predecessor raw model bytes are invalid")
    try:
        raw_xray = base64.b64decode(encoded, validate=True)
    except ValueError as error:
        raise ValueError("X-Ray predecessor raw model base64 is invalid") from error
    if hashlib.sha256(raw_xray).hexdigest() != digest:
        raise ValueError("X-Ray predecessor raw model digest changed")
    if len(raw_xray) != byte_count:
        raise ValueError("X-Ray predecessor raw model byte count changed")
    try:
        parsed_xray = json.loads(raw_xray)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("X-Ray predecessor raw model is not JSON") from error
    canonical = json.dumps(
        parsed_xray,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if canonical != raw_xray:
        raise ValueError("X-Ray predecessor uses an unknown serializer")
    if parsed_xray != xray:
        raise ValueError("X-Ray predecessor value differs from captured bytes")

    handoff = _read_json(handoff_path)
    handoff_surface = _required(handoff, "surface", "handoff")
    if handoff_surface != surface:
        raise ValueError(f"producer handoff surface does not match candidate for {surface}")
    request_capture = _capture_identity(handoff, branch="request")
    statement_capture = _capture_identity(handoff, branch="statement")
    if request_capture != statement_capture:
        raise ValueError(f"producer handoff capture identity does not agree for {surface}")
    for field in _CAPTURE_IDENTITY_FIELDS:
        _required(request_capture, field, "handoff.request.workflow_capture")
    if request_capture["surface"] != surface:
        raise ValueError(f"producer handoff capture surface does not match candidate for {surface}")
    if request_capture["case_id"] != _CASE_IDS[surface]:
        raise ValueError(f"producer handoff case does not match candidate for {surface}")
    for source_field, handoff_value in (
        ("run_id", request_capture["run_id"]),
        ("process_id", _required(handoff["request"], "task_id", "handoff.request")),
        (
            "document_id",
            _required(handoff["request"], "document_id", "handoff.request"),
        ),
    ):
        if source[source_field] != handoff_value:
            raise ValueError(f"X-Ray predecessor source.{source_field} does not match handoff")


def _xray_predecessor_candidates(
    *,
    candidate_manifest: dict[str, typing.Any],
    candidate_root: Path,
) -> dict[str, tuple[dict[str, typing.Any], Path]]:
    candidates: dict[str, tuple[dict[str, typing.Any], Path]] = {}
    expected_suffix = "/internal_arcadia_agent_load_xray.xray.json"
    for entry in candidate_manifest["candidates"]:
        if entry.get("artifact_name") != _XRAY_ARTIFACT:
            continue
        surface = str(entry.get("surface") or "")
        source_path = _resolve_inside(candidate_root, entry["candidate_path"])
        source_digest = _sha256(source_path) if source_path.exists() else None
        if source_digest != entry.get("sha256") or source_digest != entry.get("source_sha256"):
            raise ValueError(f"X-Ray predecessor source hash does not match for {surface}")
        matching = [
            value
            for value in entry.get("next_boundary_inputs", [])
            if str(value.get("candidate_path") or "").startswith("groundx-python/")
            and str(value.get("candidate_path") or "").endswith(expected_suffix)
        ]
        if len(matching) != 1:
            raise ValueError(f"X-Ray predecessor consumer input missing for {surface}")
        consumer = matching[0]
        consumer_path = _resolve_inside(candidate_root, consumer["candidate_path"])
        if not consumer_path.exists() or _sha256(consumer_path) != consumer.get("sha256"):
            raise ValueError(f"X-Ray predecessor hash does not match for {surface}")
        if consumer_path.read_bytes() != source_path.read_bytes():
            raise ValueError("X-Ray predecessor consumer bytes differ from captured source")
        if surface in candidates:
            raise ValueError(f"duplicate X-Ray predecessor candidate for {surface}")
        candidates[surface] = (entry, consumer_path)
    return candidates


def _producer_handoff_candidates(
    *,
    candidate_manifest: dict[str, typing.Any],
    candidate_root: Path,
) -> dict[str, tuple[dict[str, typing.Any], Path]]:
    handoffs: dict[str, tuple[dict[str, typing.Any], Path]] = {}
    expected_suffix = "/internal_arcadia_download_workflow_load.handoff.json"
    for entry in candidate_manifest["candidates"]:
        if entry.get("artifact_name") != _HANDOFF_ARTIFACT:
            continue
        surface = str(entry.get("surface") or "")
        source_path = _resolve_inside(candidate_root, entry["candidate_path"])
        source_digest = _sha256(source_path) if source_path.exists() else None
        if source_digest != entry.get("sha256") or source_digest != entry.get("source_sha256"):
            raise ValueError(f"producer handoff source hash does not match for {surface}")
        matching = [
            value
            for value in entry.get("next_boundary_inputs", [])
            if str(value.get("candidate_path") or "").startswith("groundx-python/")
            and str(value.get("candidate_path") or "").endswith(expected_suffix)
        ]
        if len(matching) != 1:
            raise ValueError(f"proposed producer handoff missing for {surface}")
        candidate = matching[0]
        path = _resolve_inside(candidate_root, candidate["candidate_path"])
        if not path.exists() or _sha256(path) != candidate.get("sha256"):
            raise ValueError(f"proposed producer handoff hash does not match for {surface}")
        if path.read_bytes() != source_path.read_bytes():
            raise ValueError("producer handoff consumer bytes differ from captured source")
        if surface in handoffs:
            raise ValueError(f"duplicate proposed producer handoff for {surface}")
        handoffs[surface] = (entry, path)
    return handoffs


def _captured_complete_output_candidates(
    *,
    candidate_manifest: dict[str, typing.Any],
    candidate_root: Path,
) -> dict[str, tuple[dict[str, typing.Any], Path]]:
    outputs: dict[str, tuple[dict[str, typing.Any], Path]] = {}
    for entry in candidate_manifest["candidates"]:
        if entry.get("artifact_name") != _COMPLETE_OUTPUT_ARTIFACT:
            continue
        surface = str(entry.get("surface") or "")
        source_path = _resolve_inside(candidate_root, entry["candidate_path"])
        source_digest = _sha256(source_path) if source_path.exists() else None
        if source_digest != entry.get("sha256") or source_digest != entry.get("source_sha256"):
            raise ValueError(f"captured SDK complete output hash does not match for {surface}")
        hosted_path = entry.get("source_hosted_path")
        if not isinstance(hosted_path, str) or not hosted_path.endswith("/output.full_json.json"):
            raise ValueError(f"captured SDK complete output hosted path is invalid for {surface}")
        if surface in outputs:
            raise ValueError(f"duplicate captured SDK complete output for {surface}")
        outputs[surface] = (entry, source_path)
    return outputs


def _candidate_entry(
    *,
    surface: str,
    packet_path: Path,
    diff_path: Path,
    source: dict[str, typing.Any],
    capture_manifest: dict[str, typing.Any],
) -> dict[str, typing.Any]:
    relative_packet = (
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        f"boundary-goldens/{surface}/groundx_python_xray_reassembly.expected.json"
    )
    relative_diff = relative_packet.replace(".expected.json", ".expected.diff.json")
    relative_review = relative_packet.replace(".expected.json", ".expected.review.json")
    return {
        "surface": surface,
        "artifact_name": "groundx_python_xray_reassembly",
        "candidate_path": relative_packet,
        "proposed_fixture_path": relative_packet,
        "candidate_diff_path": relative_diff,
        "candidate_diff_sha256": _sha256(diff_path),
        "proposed_review_path": relative_review,
        "next_boundary_inputs": [],
        "seed_policy": "commit_sanitized_fixture",
        "sha256": _sha256(packet_path),
        "source_sha256": source["source_sha256"],
        "source_run_id": capture_manifest["run_id"],
        "source_run_mode": capture_manifest["run_mode"],
        "source_hosted_path": source["source_hosted_path"],
        "source_path": None,
        "source_boundary_manifest_sha256": capture_manifest["source_boundary_manifest_sha256"],
        "test_path": ("groundx-python/tests/extract/test_extraction_boundary_reassembly.py"),
    }


def _complete_actual_output_bytes(
    packet: dict[str, typing.Any],
    *,
    surface: str,
    handoff_path: Path,
    xray_path: Path,
    resolve_reviewed_complete_output: typing.Callable[..., dict[str, typing.Any]],
) -> bytes:
    present = [member for member in _COMPLETE_OUTPUT_MEMBERS if member in packet]
    if not present:
        raise ValueError("SDK expected output is summary-only; complete reviewed output bytes are required")

    output = packet.get("output")
    artifacts = packet.get("artifacts")
    assertions = packet.get("assertions")
    complete = len(present) == len(_COMPLETE_OUTPUT_MEMBERS)
    previous_artifact = artifacts.get("previous_download_workflow_load") if isinstance(artifacts, dict) else None
    xray_artifact = artifacts.get("xray_predecessor") if isinstance(artifacts, dict) else None
    exact_binding = (
        packet.get("schema_version") == "groundx-python-xray-reassembly-boundary-v1"
        and packet.get("surface") == surface
        and packet.get("stage") == "groundx_python_xray_reassembly"
        and packet.get("input_from") == "internal_arcadia_download_workflow_load"
        and packet.get("input_sha256") == _sha256(handoff_path)
        and isinstance(previous_artifact, dict)
        and previous_artifact.get("sha256") == _sha256(handoff_path)
        and isinstance(xray_artifact, dict)
        and xray_artifact.get("sha256") == _sha256(xray_path)
        and isinstance(assertions, dict)
        and assertions.get("consumes_download_workflow_load_handoff") is True
        and assertions.get("consumes_exact_xray_predecessor") is True
    )
    exact_summary = (
        isinstance(output, dict)
        and output.get("workflow_output_sha256") == _sha256_json(packet.get("workflow_output"))
        and output.get("relationship_output_sha256") == _sha256_json(packet.get("relationship_output"))
        and output.get("final_output_sha256") == _sha256_json(packet.get("final_output"))
        and isinstance(packet.get("diagnostics"), list)
        and output.get("diagnostic_count") == len(packet["diagnostics"])
        and isinstance(packet.get("source_provenance"), list)
        and output.get("source_provenance_count") == len(packet["source_provenance"])
    )
    if not complete or not exact_binding or not exact_summary:
        raise ValueError("SDK expected output is reconstructed; exact reviewed output bytes are required")
    complete_output = {member: packet[member] for member in _COMPLETE_OUTPUT_MEMBERS}
    raw = _canonical_json_bytes(complete_output)
    resolved = resolve_reviewed_complete_output(raw, downloader=_reject_remote_candidate)
    if resolved != complete_output:
        raise ValueError("SDK expected output is reconstructed; exact reviewed output bytes are required")
    return raw


def _validate_captured_complete_output(
    raw: bytes,
    *,
    resolve_reviewed_complete_output: typing.Callable[..., dict[str, typing.Any]],
) -> dict[str, typing.Any]:
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("SDK expected output is reconstructed; exact reviewed output bytes are required") from error
    if not isinstance(parsed, dict) or not any(member in parsed for member in _COMPLETE_OUTPUT_MEMBERS):
        raise ValueError("SDK expected output is summary-only; complete reviewed output bytes are required")
    try:
        return resolve_reviewed_complete_output(raw, downloader=_reject_remote_candidate)
    except ValueError as error:
        raise ValueError("SDK expected output is reconstructed; exact reviewed output bytes are required") from error


def _sha256_json(value: typing.Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_json_bytes(value: typing.Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _reject_remote_candidate(_url: str) -> bytes:
    raise OSError("candidate generation is offline")


def build_candidates(
    *,
    repo_root: Path,
    xray_candidate_manifest_path: Path,
    candidate_root: Path,
    surfaces: tuple[str, ...],
) -> Path:
    if candidate_root.exists() and any(candidate_root.iterdir()):
        raise ValueError("candidate root must be empty")

    capture_manifest = _read_json(xray_candidate_manifest_path)
    if capture_manifest.get("schema_version") != "extraction_boundary_fixture_candidate_v1":
        raise ValueError("invalid X-Ray candidate manifest schema")
    if capture_manifest.get("status") != "pending_review":
        raise ValueError("X-Ray candidate manifest must be pending review")
    capture_root = xray_candidate_manifest_path.parent
    xray_predecessors = _xray_predecessor_candidates(
        candidate_manifest=capture_manifest,
        candidate_root=capture_root,
    )
    producer_handoffs = _producer_handoff_candidates(
        candidate_manifest=capture_manifest,
        candidate_root=capture_root,
    )
    captured_outputs = _captured_complete_output_candidates(
        candidate_manifest=capture_manifest,
        candidate_root=capture_root,
    )
    missing_xray = sorted(set(surfaces) - set(xray_predecessors))
    if missing_xray:
        raise ValueError(f"X-Ray predecessors missing surfaces: {', '.join(missing_xray)}")
    missing_handoffs = sorted(set(surfaces) - set(producer_handoffs))
    if missing_handoffs:
        raise ValueError("proposed producer handoffs missing surfaces: " + ", ".join(missing_handoffs))

    for surface in surfaces:
        xray_entry, xray_path = xray_predecessors[surface]
        handoff_entry, handoff_path = producer_handoffs[surface]
        _validate_candidate_pair(
            manifest=capture_manifest,
            surface=surface,
            xray_entry=xray_entry,
            xray_path=xray_path,
            handoff_entry=handoff_entry,
            handoff_path=handoff_path,
        )
        if surface in captured_outputs:
            _validate_entry_provenance(
                entry=captured_outputs[surface][0],
                manifest=capture_manifest,
                label="captured SDK complete output",
            )

    missing_outputs = sorted(set(surfaces) - set(captured_outputs))
    if missing_outputs:
        raise ValueError(
            "INTENTIONAL RED: captured SDK complete outputs missing surfaces: "
            + ", ".join(missing_outputs)
            + "; capture canonical five-member internal_arcadia_sdk_reassembly_output "
            "output.full_json.json from the same Arcadia run"
        )

    replay = _load_replay_module(repo_root)
    replay_inputs = _load_replay_inputs_module(repo_root)
    replay._real_xray_predecessor_path = lambda surface: xray_predecessors[surface][1]
    replay._real_download_workflow_load_input_path = lambda surface: producer_handoffs[surface][1]
    prepared = []
    for surface in surfaces:
        actual, accepted_path, _unused_diff_path = replay._build_xray_reassembly_boundary_artifact(
            candidate_root, surface
        )
        packet = replay._stable_boundary_output(actual)
        actual_complete_bytes = _complete_actual_output_bytes(
            packet,
            surface=surface,
            handoff_path=producer_handoffs[surface][1],
            xray_path=xray_predecessors[surface][1],
            resolve_reviewed_complete_output=replay_inputs.resolve_reviewed_complete_output,
        )
        captured_entry, captured_path = captured_outputs[surface]
        captured_bytes = captured_path.read_bytes()
        captured_packet = _validate_captured_complete_output(
            captured_bytes,
            resolve_reviewed_complete_output=replay_inputs.resolve_reviewed_complete_output,
        )
        if actual_complete_bytes != captured_bytes:
            raise ValueError(f"SDK production reassembly differs from captured complete output for {surface}")
        prepared.append((surface, captured_packet, captured_bytes, accepted_path, captured_entry))

    candidate_root.mkdir(parents=True, exist_ok=True)
    candidates = []
    for surface, packet, packet_bytes, accepted_path, captured_entry in prepared:
        relative_packet = Path(
            "groundx-python/tests/extract/fixtures/extraction-boundary/"
            f"boundary-goldens/{surface}/groundx_python_xray_reassembly.expected.json"
        )
        packet_path = candidate_root / relative_packet
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_bytes(packet_bytes)

        accepted = _read_json(accepted_path) if accepted_path.exists() else None
        diff_path = packet_path.with_name("groundx_python_xray_reassembly.expected.diff.json")
        _write_json(
            diff_path,
            {
                "kind": "machine_readable_json_diff",
                "status": "pending_review",
                "artifact_name": "groundx_python_xray_reassembly",
                "candidate_sha256": _sha256(packet_path),
                "current_accepted_sha256": (_sha256(accepted_path) if accepted_path.exists() else None),
                "source_artifact_sha256": xray_predecessors[surface][0]["source_sha256"],
                "source_run_id": capture_manifest["run_id"],
                "changes": _changes(accepted, packet),
            },
        )
        candidates.append(
            _candidate_entry(
                surface=surface,
                packet_path=packet_path,
                diff_path=diff_path,
                source=captured_entry,
                capture_manifest=capture_manifest,
            )
        )

    manifest_path = candidate_root / "fixture_candidate_manifest.json"
    _write_json(
        manifest_path,
        {
            "schema_version": "extraction_boundary_fixture_candidate_v1",
            "status": "pending_review",
            "run_id": capture_manifest["run_id"],
            "run_mode": capture_manifest["run_mode"],
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "artifact_catalog_version": capture_manifest["artifact_catalog_version"],
            "artifact_catalog_sha256": capture_manifest["artifact_catalog_sha256"],
            "source_boundary_manifest_sha256": capture_manifest["source_boundary_manifest_sha256"],
            "upstream_candidate_manifest_sha256": _sha256(xray_candidate_manifest_path),
            "generator": {
                "candidate_builder_sha256": _sha256(Path(__file__)),
                "boundary_replay_sha256": _sha256(
                    repo_root / "tests" / "extract" / "test_extraction_boundary_reassembly.py"
                ),
                "production_reassembly_sha256": _sha256(
                    repo_root / "src" / "groundx" / "extract" / "custom_outputs.py"
                ),
            },
            "candidates": candidates,
            "private_references": [],
        },
    )
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xray-candidate-manifest", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--surfaces")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    try:
        manifest_path = build_candidates(
            repo_root=repo_root,
            xray_candidate_manifest_path=args.xray_candidate_manifest.resolve(),
            candidate_root=args.candidate_root.resolve(),
            surfaces=_selected_surfaces(args.surfaces),
        )
    except (KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(manifest_path)


if __name__ == "__main__":
    main()
