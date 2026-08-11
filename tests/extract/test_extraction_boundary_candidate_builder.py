import base64
import hashlib
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tests" / "extract" / "build_extraction_boundary_candidates.py"
SURFACE = "arcadia_legacy"
BOUNDARY_ROOT = REPO_ROOT / "tests" / "extract" / "fixtures" / "extraction-boundary"
RUN_ID = "20260810T201159Z"
RUN_MODE = "fixture_seeding"
BOUNDARY_MANIFEST_SHA256 = "b" * 64
XRAY_ARTIFACT = "internal_arcadia_load_xray_predecessor"
HANDOFF_ARTIFACT = "internal_arcadia_download_workflow_load"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_canonical_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _complete_output_values() -> dict[str, object]:
    return {
        "workflow_output": {"statement": {"value": "candidate"}},
        "relationship_output": {"relationships": []},
        "final_output": {"statement": {"value": "candidate"}},
        "diagnostics": [],
        "source_provenance": [],
    }


def _complete_candidate_packet(
    *,
    surface: str,
    handoff_path: Path,
    xray_path: Path,
) -> dict[str, object]:
    complete_output = _complete_output_values()
    return {
        "schema_version": "groundx-python-xray-reassembly-boundary-v1",
        "surface": surface,
        "stage": "groundx_python_xray_reassembly",
        "input_from": "internal_arcadia_download_workflow_load",
        "input_sha256": _sha256(handoff_path),
        **complete_output,
        "output": {
            "workflow_output_sha256": _sha256_json(complete_output["workflow_output"]),
            "relationship_output_sha256": _sha256_json(complete_output["relationship_output"]),
            "final_output_sha256": _sha256_json(complete_output["final_output"]),
            "diagnostic_count": 0,
            "source_provenance_count": 0,
        },
        "artifacts": {
            "previous_download_workflow_load": {"sha256": _sha256(handoff_path)},
            "xray_predecessor": {"sha256": _sha256(xray_path)},
        },
        "assertions": {
            "consumes_download_workflow_load_handoff": True,
            "consumes_exact_xray_predecessor": True,
        },
    }


def _load_builder_module():
    spec = importlib.util.spec_from_file_location(
        "extraction_boundary_candidate_builder",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder


def _capture_identity(surface: str) -> dict[str, object]:
    case_id = surface.replace("_", "-")
    return {
        "bucket_id": 12345,
        "capture_config_hash": "e" * 64,
        "case_id": case_id,
        "enabled": True,
        "run_id": f"extract-cert-{case_id}-01",
        "schema_version": "extraction_pipeline_capture_v1",
        "surface": surface,
        "workflow_id": "11111111-2222-3333-4444-555555555555",
    }


def _proposed_handoff_candidate(
    root: Path,
    surface: str,
    *,
    packet: dict[str, object] | None = None,
) -> tuple[dict[str, object], Path]:
    source_relative = Path(
        "internal-arcadia-agents/testdata/extraction-boundary/"
        f"boundary-goldens/{surface}/internal_arcadia_download_workflow_load.expected.json"
    )
    relative = Path(
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        f"inputs/{surface}/internal_arcadia_download_workflow_load.handoff.json"
    )
    target = root / relative
    if packet is None:
        packet = {
            "schema_version": "internal-arcadia-download-workflow-load-v1",
            "surface": surface,
            "stage": "internal_arcadia_download_workflow_load",
            "request": {},
            "statement": {},
            "workflow_extract": {"workflow": {"output_routes": []}},
            "workflow_schema_hash": "f" * 64,
        }
    packet["surface"] = surface
    capture_identity = _capture_identity(surface)
    request = packet.setdefault("request", {})
    statement = packet.setdefault("statement", {})
    assert isinstance(request, dict)
    assert isinstance(statement, dict)
    request["workflow_capture"] = capture_identity
    statement["workflow_capture"] = dict(capture_identity)
    request["task_id"] = "task-1"
    request["document_id"] = "document-1"
    statement["task_id"] = "task-1"
    statement["document_id"] = "document-1"
    _write_json(target, packet)
    source_target = root / source_relative
    source_target.parent.mkdir(parents=True, exist_ok=True)
    source_target.write_bytes(target.read_bytes())
    entry: dict[str, object] = {
        "surface": surface,
        "artifact_name": HANDOFF_ARTIFACT,
        "candidate_path": str(source_relative),
        "sha256": _sha256(source_target),
        "source_sha256": _sha256(source_target),
        "source_run_id": RUN_ID,
        "source_run_mode": RUN_MODE,
        "source_boundary_manifest_sha256": BOUNDARY_MANIFEST_SHA256,
        "next_boundary_inputs": [
            {
                "candidate_path": str(relative),
                "sha256": _sha256(target),
            }
        ],
    }
    return entry, target


def _proposed_xray_candidate(
    root: Path,
    surface: str,
    *,
    xray: object | None = None,
) -> tuple[dict[str, object], Path]:
    source_relative = Path(
        "internal-arcadia-agents/testdata/extraction-boundary/"
        f"inputs/{surface}/internal_arcadia_agent_load_xray.xray.json"
    )
    relative = Path(
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        f"inputs/{surface}/internal_arcadia_agent_load_xray.xray.json"
    )
    target = root / relative
    if xray is None:
        xray = {
            "sourceUrl": "https://upload.test/document.json",
            "documentPages": [
                {
                    "pageNumber": 1,
                    "pageUrl": "https://upload.test/page-1.png",
                    "height": 100,
                    "width": 80,
                    "customSectionOutputs": {"complete": {"value": "kept"}},
                }
            ],
        }
    raw_xray = json.dumps(
        xray,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    packet = {
        "kind": "xray_predecessor",
        "metadata": {},
        "raw_xray_model_base64": base64.b64encode(raw_xray).decode("ascii"),
        "raw_xray_model_bytes": len(raw_xray),
        "raw_xray_model_sha256": hashlib.sha256(raw_xray).hexdigest(),
        "source": {
            "source_kind": "live_capture",
            "run_id": _capture_identity(surface)["run_id"],
            "process_id": "task-1",
            "document_id": "document-1",
        },
        "value": xray,
    }
    _write_json(target, packet)
    source_target = root / source_relative
    source_target.parent.mkdir(parents=True, exist_ok=True)
    source_target.write_bytes(target.read_bytes())
    entry: dict[str, object] = {
        "surface": surface,
        "artifact_name": XRAY_ARTIFACT,
        "candidate_path": str(source_relative),
        "sha256": _sha256(source_target),
        "source_sha256": _sha256(source_target),
        "source_run_id": RUN_ID,
        "source_run_mode": RUN_MODE,
        "source_hosted_path": "layout/processed/task/document-trace/input.xray.json",
        "source_boundary_manifest_sha256": BOUNDARY_MANIFEST_SHA256,
        "next_boundary_inputs": [
            {
                "candidate_path": str(relative),
                "sha256": _sha256(target),
            }
        ],
    }
    return entry, target


def _captured_complete_output_candidate(
    root: Path,
    surface: str,
    complete_output: object,
) -> tuple[dict[str, object], Path]:
    relative = Path(
        "internal-arcadia-agents/testdata/extraction-boundary/"
        f"captured/{surface}/internal_arcadia_sdk_reassembly_output.output.full_json.json"
    )
    target = root / relative
    _write_canonical_json(target, complete_output)
    entry: dict[str, object] = {
        "surface": surface,
        "artifact_name": "internal_arcadia_sdk_reassembly_output",
        "candidate_path": str(relative),
        "sha256": _sha256(target),
        "source_sha256": _sha256(target),
        "source_run_id": RUN_ID,
        "source_run_mode": RUN_MODE,
        "source_hosted_path": (
            f"layout/processed/task-1/document-1-extract-trace/internal-arcadia-agents/{surface}/output.full_json.json"
        ),
        "source_boundary_manifest_sha256": BOUNDARY_MANIFEST_SHA256,
        "next_boundary_inputs": [],
    }
    return entry, target


def _coherent_candidate_manifest(
    root: Path,
    surface: str,
    *,
    xray: object | None = None,
    handoff: dict[str, object] | None = None,
    captured_complete_output: object | None = None,
) -> tuple[Path, dict[str, object], Path, Path]:
    xray_entry, xray_path = _proposed_xray_candidate(root, surface, xray=xray)
    handoff_entry, handoff_path = _proposed_handoff_candidate(
        root,
        surface,
        packet=handoff,
    )
    candidates = [xray_entry, handoff_entry]
    if captured_complete_output is not None:
        output_entry, _output_path = _captured_complete_output_candidate(
            root,
            surface,
            captured_complete_output,
        )
        candidates.append(output_entry)
    manifest: dict[str, object] = {
        "schema_version": "extraction_boundary_fixture_candidate_v1",
        "status": "pending_review",
        "run_id": RUN_ID,
        "run_mode": RUN_MODE,
        "artifact_catalog_version": "2026-07-23.1",
        "artifact_catalog_sha256": "a" * 64,
        "source_boundary_manifest_sha256": BOUNDARY_MANIFEST_SHA256,
        "candidates": candidates,
    }
    path = root / "fixture_candidate_manifest.json"
    _write_json(path, manifest)
    return path, manifest, xray_path, handoff_path


def _candidate_entry(
    manifest: dict[str, object],
    artifact_name: str,
) -> dict[str, object]:
    candidates = manifest["candidates"]
    assert isinstance(candidates, list)
    return next(
        entry for entry in candidates if isinstance(entry, dict) and entry.get("artifact_name") == artifact_name
    )


def _refresh_candidate_hash(
    manifest: dict[str, object],
    artifact_name: str,
    path: Path,
    *,
    sync_xray_source: bool = True,
    sync_handoff_source: bool = True,
) -> None:
    entry = _candidate_entry(manifest, artifact_name)
    if artifact_name == XRAY_ARTIFACT:
        next_inputs = entry["next_boundary_inputs"]
        assert isinstance(next_inputs, list) and isinstance(next_inputs[0], dict)
        next_inputs[0]["sha256"] = _sha256(path)
        if sync_xray_source:
            consumer_relative = Path(str(next_inputs[0]["candidate_path"]))
            candidate_root = path
            for _part in consumer_relative.parts:
                candidate_root = candidate_root.parent
            source_path = candidate_root / str(entry["candidate_path"])
            source_path.write_bytes(path.read_bytes())
            entry["sha256"] = _sha256(source_path)
            entry["source_sha256"] = _sha256(source_path)
        return
    next_inputs = entry["next_boundary_inputs"]
    assert isinstance(next_inputs, list) and isinstance(next_inputs[0], dict)
    next_inputs[0]["sha256"] = _sha256(path)
    if sync_handoff_source:
        consumer_relative = Path(str(next_inputs[0]["candidate_path"]))
        candidate_root = path
        for _part in consumer_relative.parts:
            candidate_root = candidate_root.parent
        source_path = candidate_root / str(entry["candidate_path"])
        source_path.write_bytes(path.read_bytes())
        entry["sha256"] = _sha256(source_path)
        entry["source_sha256"] = _sha256(source_path)


def _assert_rejected_before_writes(
    *,
    tmp_path: Path,
    monkeypatch,
    manifest: dict[str, object],
    manifest_path: Path,
    expected_error: str,
) -> None:
    _write_json(manifest_path, manifest)
    accepted_output = tmp_path / "accepted.json"
    _write_json(accepted_output, {"surface": SURFACE})
    replay = types.SimpleNamespace(
        _build_xray_reassembly_boundary_artifact=(
            lambda _candidate_root, surface: (
                {"surface": surface},
                accepted_output,
                tmp_path / "unused.diff.json",
            )
        ),
        _stable_boundary_output=lambda value: value,
    )
    builder = _load_builder_module()
    monkeypatch.setattr(builder, "_load_replay_module", lambda _repo_root: replay)
    candidate_root = tmp_path / "sdk-candidates"

    with pytest.raises(ValueError) as error:
        builder.build_candidates(
            repo_root=REPO_ROOT,
            xray_candidate_manifest_path=manifest_path,
            candidate_root=candidate_root,
            surfaces=(SURFACE,),
        )

    assert expected_error in str(error.value)
    assert not candidate_root.exists()


def test_builder_default_surfaces_follow_projection_order(monkeypatch) -> None:
    projection = {
        "cases": [
            {"id": "third-case", "surface": "third"},
            {"id": "first-case", "surface": "first"},
        ]
    }
    original_read_text = Path.read_text
    catalog_path = BOUNDARY_ROOT / "catalog.json"

    def read_text(path: Path, *args, **kwargs):
        if path == catalog_path:
            return json.dumps(projection)
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    builder = _load_builder_module()

    assert builder.SURFACES == ("third", "first")
    assert builder._selected_surfaces(None) == ("third", "first")


def test_builder_is_intentionally_red_without_captured_complete_output(
    tmp_path: Path,
) -> None:
    capture_root = tmp_path / "captured-boundaries"
    capture_manifest, _manifest, candidate_xray, _handoff_path = _coherent_candidate_manifest(capture_root, SURFACE)

    candidate_root = tmp_path / "sdk-candidates"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--xray-candidate-manifest",
            str(capture_manifest),
            "--candidate-root",
            str(candidate_root),
            "--surfaces",
            SURFACE,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode != 0
    assert (
        "INTENTIONAL RED: captured SDK complete outputs missing surfaces: arcadia_legacy; "
        "capture canonical five-member internal_arcadia_sdk_reassembly_output "
        "output.full_json.json from the same Arcadia run"
    ) in result.stderr
    assert not candidate_root.exists()
    assert candidate_xray.exists()


def test_builder_rejects_a_nonempty_candidate_root(tmp_path: Path) -> None:
    candidate_root = tmp_path / "sdk-candidates"
    candidate_root.mkdir()
    (candidate_root / "existing.json").write_text("{}\n")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--xray-candidate-manifest",
            str(tmp_path / "missing.json"),
            "--candidate-root",
            str(candidate_root),
            "--surfaces",
            SURFACE,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode != 0
    assert "candidate root must be empty" in result.stderr


@pytest.mark.parametrize(
    ("provenance_source", "expected_error"),
    [
        (
            XRAY_ARTIFACT,
            "X-Ray predecessor candidate source_run_id does not match manifest",
        ),
        (HANDOFF_ARTIFACT, "producer handoff source_run_id does not match manifest"),
        ("xray_source", "X-Ray predecessor source.run_id does not match handoff"),
        ("workflow_capture", "producer handoff capture identity does not agree"),
    ],
)
def test_builder_rejects_cross_run_candidate_pairs_before_writes(
    tmp_path: Path,
    monkeypatch,
    provenance_source: str,
    expected_error: str,
) -> None:
    sidecar_root = tmp_path / "provider-candidates"
    manifest_path, manifest, xray_path, handoff_path = _coherent_candidate_manifest(
        sidecar_root,
        SURFACE,
    )
    if provenance_source in {XRAY_ARTIFACT, HANDOFF_ARTIFACT}:
        _candidate_entry(manifest, provenance_source)["source_run_id"] = "older-run"
    elif provenance_source == "xray_source":
        packet = json.loads(xray_path.read_text())
        packet["source"]["run_id"] = "older-run"
        _write_json(xray_path, packet)
        _refresh_candidate_hash(manifest, XRAY_ARTIFACT, xray_path)
    else:
        packet = json.loads(handoff_path.read_text())
        packet["statement"]["workflow_capture"]["run_id"] = "older-capture-run"
        _write_json(handoff_path, packet)
        _refresh_candidate_hash(manifest, HANDOFF_ARTIFACT, handoff_path)

    _assert_rejected_before_writes(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        manifest=manifest,
        manifest_path=manifest_path,
        expected_error=expected_error,
    )


@pytest.mark.parametrize(
    "surface_source",
    ["handoff", "workflow_capture"],
)
def test_builder_rejects_wrong_surface_candidate_pairs_before_writes(
    tmp_path: Path,
    monkeypatch,
    surface_source: str,
) -> None:
    sidecar_root = tmp_path / "provider-candidates"
    manifest_path, manifest, xray_path, handoff_path = _coherent_candidate_manifest(
        sidecar_root,
        SURFACE,
    )
    packet = json.loads(handoff_path.read_text())
    if surface_source == "handoff":
        packet["surface"] = "generic_v1"
        expected_error = "producer handoff surface does not match candidate"
    else:
        packet["request"]["workflow_capture"]["surface"] = "generic_v1"
        packet["statement"]["workflow_capture"]["surface"] = "generic_v1"
        expected_error = "producer handoff capture surface does not match candidate"
    _write_json(handoff_path, packet)
    _refresh_candidate_hash(manifest, HANDOFF_ARTIFACT, handoff_path)

    _assert_rejected_before_writes(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        manifest=manifest,
        manifest_path=manifest_path,
        expected_error=expected_error,
    )


@pytest.mark.parametrize(
    ("field_path", "value", "expected_error"),
    [
        (("kind",), "rebuilt_sidecar", "X-Ray predecessor kind is invalid"),
        (
            ("source", "source_kind"),
            "repo_fixture",
            "X-Ray predecessor is not a live capture",
        ),
        (
            ("raw_xray_model_sha256",),
            "0" * 64,
            "X-Ray predecessor raw model digest changed",
        ),
        (
            ("raw_xray_model_bytes",),
            1,
            "X-Ray predecessor raw model byte count changed",
        ),
        (
            ("value", "documentPages", 0, "customSectionOutputs"),
            {},
            "X-Ray predecessor value differs from captured bytes",
        ),
    ],
)
def test_builder_rejects_rebuilt_or_changed_xray_envelopes_before_writes(
    tmp_path: Path,
    monkeypatch,
    field_path: tuple[object, ...],
    value: object,
    expected_error: str,
) -> None:
    sidecar_root = tmp_path / "provider-candidates"
    manifest_path, manifest, xray_path, _handoff_path = _coherent_candidate_manifest(
        sidecar_root,
        SURFACE,
    )
    packet = json.loads(xray_path.read_text())
    cursor: object = packet
    for key in field_path[:-1]:
        if isinstance(cursor, list):
            assert isinstance(key, int)
            cursor = cursor[key]
        else:
            assert isinstance(cursor, dict)
            assert isinstance(key, str)
            cursor = cursor[key]
    final = field_path[-1]
    if isinstance(cursor, list):
        assert isinstance(final, int)
        cursor[final] = value
    else:
        assert isinstance(cursor, dict)
        assert isinstance(final, str)
        cursor[final] = value
    _write_json(xray_path, packet)
    _refresh_candidate_hash(manifest, XRAY_ARTIFACT, xray_path)

    _assert_rejected_before_writes(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        manifest=manifest,
        manifest_path=manifest_path,
        expected_error=expected_error,
    )


def test_builder_rejects_a_consumer_xray_copy_that_differs_from_its_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_root = tmp_path / "provider-candidates"
    manifest_path, manifest, xray_path, _handoff_path = _coherent_candidate_manifest(
        source_root,
        SURFACE,
    )
    packet = json.loads(xray_path.read_text())
    packet["value"]["documentPages"][0]["customSectionOutputs"] = {"omitted": True}
    raw = json.dumps(
        packet["value"],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    packet["raw_xray_model_base64"] = base64.b64encode(raw).decode("ascii")
    packet["raw_xray_model_bytes"] = len(raw)
    packet["raw_xray_model_sha256"] = hashlib.sha256(raw).hexdigest()
    _write_json(xray_path, packet)
    _refresh_candidate_hash(
        manifest,
        XRAY_ARTIFACT,
        xray_path,
        sync_xray_source=False,
    )

    _assert_rejected_before_writes(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        manifest=manifest,
        manifest_path=manifest_path,
        expected_error="X-Ray predecessor consumer bytes differ from captured source",
    )


def test_builder_rejects_a_consumer_handoff_copy_that_differs_from_its_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_root = tmp_path / "provider-candidates"
    manifest_path, manifest, _xray_path, handoff_path = _coherent_candidate_manifest(
        source_root,
        SURFACE,
    )
    packet = json.loads(handoff_path.read_text())
    packet["workflow_schema_hash"] = "0" * 64
    _write_json(handoff_path, packet)
    _refresh_candidate_hash(
        manifest,
        HANDOFF_ARTIFACT,
        handoff_path,
        sync_handoff_source=False,
    )

    _assert_rejected_before_writes(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        manifest=manifest,
        manifest_path=manifest_path,
        expected_error="producer handoff consumer bytes differ from captured source",
    )


@pytest.mark.parametrize("artifact_name", [XRAY_ARTIFACT, HANDOFF_ARTIFACT])
@pytest.mark.parametrize(
    "field",
    ["source_run_mode", "source_boundary_manifest_sha256"],
)
def test_builder_rejects_entry_manifest_provenance_mismatches_before_writes(
    tmp_path: Path,
    monkeypatch,
    artifact_name: str,
    field: str,
) -> None:
    sidecar_root = tmp_path / "provider-candidates"
    manifest_path, manifest, _xray_path, _handoff_path = _coherent_candidate_manifest(
        sidecar_root,
        SURFACE,
    )
    _candidate_entry(manifest, artifact_name)[field] = "mismatch"
    label = "X-Ray predecessor candidate" if artifact_name == XRAY_ARTIFACT else "producer handoff"

    _assert_rejected_before_writes(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        manifest=manifest,
        manifest_path=manifest_path,
        expected_error=f"{label} {field} does not match manifest",
    )


@pytest.mark.parametrize(
    ("field", "expected_error"),
    [
        ("run_id", "X-Ray predecessor source.run_id is required"),
        ("process_id", "X-Ray predecessor source.process_id is required"),
        ("document_id", "X-Ray predecessor source.document_id is required"),
    ],
)
def test_builder_requires_complete_xray_source_identity_before_writes(
    tmp_path: Path,
    monkeypatch,
    field: str,
    expected_error: str,
) -> None:
    sidecar_root = tmp_path / "provider-candidates"
    manifest_path, manifest, xray_path, _handoff_path = _coherent_candidate_manifest(
        sidecar_root,
        SURFACE,
    )
    packet = json.loads(xray_path.read_text())
    del packet["source"][field]
    _write_json(xray_path, packet)
    _refresh_candidate_hash(manifest, XRAY_ARTIFACT, xray_path)

    _assert_rejected_before_writes(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        manifest=manifest,
        manifest_path=manifest_path,
        expected_error=expected_error,
    )


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "run_id",
        "case_id",
        "bucket_id",
        "workflow_id",
        "capture_config_hash",
    ],
)
def test_builder_requires_complete_producer_capture_identity_before_writes(
    tmp_path: Path,
    monkeypatch,
    field: str,
) -> None:
    sidecar_root = tmp_path / "provider-candidates"
    manifest_path, manifest, _xray_path, handoff_path = _coherent_candidate_manifest(
        sidecar_root,
        SURFACE,
    )
    packet = json.loads(handoff_path.read_text())
    del packet["request"]["workflow_capture"][field]
    del packet["statement"]["workflow_capture"][field]
    _write_json(handoff_path, packet)
    _refresh_candidate_hash(manifest, HANDOFF_ARTIFACT, handoff_path)

    _assert_rejected_before_writes(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        manifest=manifest,
        manifest_path=manifest_path,
        expected_error=f"handoff.request.workflow_capture.{field} is required",
    )


@pytest.mark.parametrize(
    "missing_field",
    [
        "manifest.run_id",
        "manifest.run_mode",
        "manifest.source_boundary_manifest_sha256",
        "xray_entry.source_run_id",
        "xray_entry.source_run_mode",
        "xray_entry.source_boundary_manifest_sha256",
        "handoff_entry.source_run_id",
        "handoff_entry.source_run_mode",
        "handoff_entry.source_boundary_manifest_sha256",
        "envelope.kind",
        "envelope.source.run_id",
        "envelope.raw_xray_model_base64",
        "envelope.raw_xray_model_sha256",
        "envelope.raw_xray_model_bytes",
        "envelope.value",
        "handoff.surface",
        "handoff.request.workflow_capture",
        "handoff.statement.workflow_capture",
    ],
)
def test_builder_requires_complete_coherence_metadata_before_writes(
    tmp_path: Path,
    monkeypatch,
    missing_field: str,
) -> None:
    sidecar_root = tmp_path / "provider-candidates"
    manifest_path, manifest, xray_path, handoff_path = _coherent_candidate_manifest(
        sidecar_root,
        SURFACE,
    )
    owner, *path = missing_field.split(".")
    if owner in {"envelope", "handoff"}:
        payload_path = xray_path if owner == "envelope" else handoff_path
        packet = json.loads(payload_path.read_text())
        cursor = packet
        for key in path[:-1]:
            cursor = cursor[key]
        del cursor[path[-1]]
        _write_json(payload_path, packet)
        artifact_name = XRAY_ARTIFACT if owner == "envelope" else HANDOFF_ARTIFACT
        _refresh_candidate_hash(manifest, artifact_name, payload_path)
    else:
        target = (
            manifest
            if owner == "manifest"
            else _candidate_entry(
                manifest,
                XRAY_ARTIFACT if owner == "xray_entry" else HANDOFF_ARTIFACT,
            )
        )
        cursor = target
        for key in path[:-1]:
            cursor = cursor[key]
        del cursor[path[-1]]
    expected_owner = {
        "xray_entry": "X-Ray predecessor candidate",
        "handoff_entry": "producer handoff",
    }.get(owner, owner)
    expected_path = f"{expected_owner}.{'.'.join(path)} is required"
    if missing_field == "envelope.source.run_id":
        expected_path = "X-Ray predecessor source.run_id is required"

    _assert_rejected_before_writes(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        manifest=manifest,
        manifest_path=manifest_path,
        expected_error=expected_path,
    )


def test_builder_records_reassembly_when_quality_assertions_fail(
    tmp_path: Path,
    monkeypatch,
) -> None:
    surface = "adp_v1"
    capture_root = tmp_path / "captured-boundaries"
    captured_complete_output = _complete_output_values()
    capture_manifest, _manifest, xray_path, handoff_path = _coherent_candidate_manifest(
        capture_root,
        surface,
        captured_complete_output=captured_complete_output,
    )
    accepted_output = tmp_path / "accepted.json"
    _write_json(
        accepted_output,
        {
            "assertions": {"shape_contract_passed": True},
            "shape_assertions": {"has_adp_core_fields_populated_by_section": True},
        },
    )
    actual = _complete_candidate_packet(
        surface=surface,
        handoff_path=handoff_path,
        xray_path=xray_path,
    )
    assertions = actual["assertions"]
    assert isinstance(assertions, dict)
    assertions["shape_contract_passed"] = False
    actual["shape_assertions"] = {"has_adp_core_fields_populated_by_section": False}
    replay = types.SimpleNamespace(
        _build_xray_reassembly_boundary_artifact=(
            lambda _candidate_root, _surface: (
                actual,
                accepted_output,
                tmp_path / "unused.diff.json",
            )
        ),
        _stable_boundary_output=lambda value: value,
    )
    builder = _load_builder_module()
    monkeypatch.setattr(builder, "_load_replay_module", lambda _repo_root: replay)
    candidate_root = tmp_path / "sdk-candidates"

    manifest_path = builder.build_candidates(
        repo_root=REPO_ROOT,
        xray_candidate_manifest_path=capture_manifest,
        candidate_root=candidate_root,
        surfaces=(surface,),
    )

    assert manifest_path == candidate_root / "fixture_candidate_manifest.json"
    candidate = json.loads(
        (
            candidate_root
            / "groundx-python"
            / "tests"
            / "extract"
            / "fixtures"
            / "extraction-boundary"
            / "boundary-goldens"
            / surface
            / "groundx_python_xray_reassembly.expected.json"
        ).read_text()
    )
    assert candidate == captured_complete_output
    captured_entry = _candidate_entry(_manifest, "internal_arcadia_sdk_reassembly_output")
    assert (
        candidate_root
        / "groundx-python"
        / "tests"
        / "extract"
        / "fixtures"
        / "extraction-boundary"
        / "boundary-goldens"
        / surface
        / "groundx_python_xray_reassembly.expected.json"
    ).read_bytes() == (capture_root / str(captured_entry["candidate_path"])).read_bytes()


@pytest.mark.parametrize(
    ("captured_output", "expected_error"),
    [
        (
            {"surface": SURFACE, "output": {"final_output_sha256": "0" * 64}},
            "SDK expected output is summary-only; complete reviewed output bytes are required",
        ),
        (
            {
                "surface": SURFACE,
                "workflow_output": {"statement": {"value": "reconstructed"}},
                "relationship_output": {"statement": {"value": "reconstructed"}},
                "final_output": {"statement": {"value": "reconstructed"}},
                "diagnostics": [],
                "source_provenance": [],
                "output": {
                    "workflow_output_sha256": "1" * 64,
                    "relationship_output_sha256": "2" * 64,
                    "final_output_sha256": "3" * 64,
                },
                "reviewed_complete_output": {},
            },
            "SDK expected output is reconstructed; exact reviewed output bytes are required",
        ),
        (
            {
                "surface": SURFACE,
                "workflow_output": {"statement": {"value": "reconstructed"}},
                "relationship_output": {"statement": {"value": "reconstructed"}},
                "final_output": {"statement": {"value": "reconstructed"}},
                "diagnostics": [],
                "source_provenance": [],
                "output": {
                    "workflow_output_sha256": "1" * 64,
                    "relationship_output_sha256": "2" * 64,
                    "final_output_sha256": "3" * 64,
                },
                "evidence_origin": "reviewed",
            },
            "SDK expected output is reconstructed; exact reviewed output bytes are required",
        ),
    ],
)
def test_builder_rejects_incomplete_or_reconstructed_expected_output(
    tmp_path: Path,
    monkeypatch,
    captured_output: dict[str, object],
    expected_error: str,
) -> None:
    capture_root = tmp_path / "captured-boundaries"
    capture_manifest, _manifest, xray_path, handoff_path = _coherent_candidate_manifest(
        capture_root,
        SURFACE,
        captured_complete_output=captured_output,
    )
    accepted_output = tmp_path / "accepted.json"
    _write_json(accepted_output, {"surface": SURFACE})
    actual = _complete_candidate_packet(
        surface=SURFACE,
        handoff_path=handoff_path,
        xray_path=xray_path,
    )
    replay = types.SimpleNamespace(
        _build_xray_reassembly_boundary_artifact=(
            lambda _candidate_root, _surface: (
                actual,
                accepted_output,
                tmp_path / "unused.diff.json",
            )
        ),
        _stable_boundary_output=lambda value: value,
    )
    builder = _load_builder_module()
    monkeypatch.setattr(builder, "_load_replay_module", lambda _repo_root: replay)
    candidate_root = tmp_path / "sdk-candidates"

    with pytest.raises(ValueError) as error:
        builder.build_candidates(
            repo_root=REPO_ROOT,
            xray_candidate_manifest_path=capture_manifest,
            candidate_root=candidate_root,
            surfaces=(SURFACE,),
        )

    assert str(error.value) == expected_error
    assert not candidate_root.exists() or not any(candidate_root.rglob("*"))


def test_builder_rejects_self_generated_complete_output_without_captured_oracle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    capture_root = tmp_path / "captured-boundaries"
    capture_manifest, _manifest, xray_path, handoff_path = _coherent_candidate_manifest(
        capture_root,
        SURFACE,
    )
    actual = _complete_candidate_packet(
        surface=SURFACE,
        handoff_path=handoff_path,
        xray_path=xray_path,
    )
    replay_called = False

    def build_from_current_replay(_candidate_root: Path, _surface: str):
        nonlocal replay_called
        replay_called = True
        return actual, tmp_path / "accepted.json", tmp_path / "unused.diff.json"

    replay = types.SimpleNamespace(
        _build_xray_reassembly_boundary_artifact=build_from_current_replay,
        _stable_boundary_output=lambda value: value,
    )
    builder = _load_builder_module()
    monkeypatch.setattr(builder, "_load_replay_module", lambda _repo_root: replay)
    candidate_root = tmp_path / "sdk-candidates"

    with pytest.raises(
        ValueError,
        match="INTENTIONAL RED: captured SDK complete outputs missing surfaces: arcadia_legacy",
    ):
        builder.build_candidates(
            repo_root=REPO_ROOT,
            xray_candidate_manifest_path=capture_manifest,
            candidate_root=candidate_root,
            surfaces=(SURFACE,),
        )

    assert replay_called is False
    assert not candidate_root.exists()


def test_builder_replays_the_proposed_producer_handoff_with_the_proposed_xray(
    tmp_path: Path,
    monkeypatch,
) -> None:
    surface = "adp_v1"
    capture_root = tmp_path / "provider-candidates"
    capture_manifest, _manifest, candidate_xray, candidate_handoff = _coherent_candidate_manifest(
        capture_root,
        surface,
        xray={"source": "proposed"},
        handoff={"request": {"source": "proposed"}},
        captured_complete_output=_complete_output_values(),
    )
    accepted_output = tmp_path / "accepted.json"
    _write_json(accepted_output, {"input_sha256": "accepted"})
    replay = types.SimpleNamespace()
    consumed: dict[str, str] = {}

    def build_candidate(_candidate_root: Path, selected_surface: str):
        producer_path = replay._real_download_workflow_load_input_path(selected_surface)
        xray_path = replay._real_xray_predecessor_path(selected_surface)
        consumed["handoff_sha256"] = _sha256(producer_path)
        consumed["xray_sha256"] = _sha256(xray_path)
        packet = _complete_candidate_packet(
            surface=selected_surface,
            handoff_path=producer_path,
            xray_path=xray_path,
        )
        return (
            packet,
            accepted_output,
            tmp_path / "unused.diff.json",
        )

    replay._build_xray_reassembly_boundary_artifact = build_candidate
    replay._stable_boundary_output = lambda value: value
    builder = _load_builder_module()
    monkeypatch.setattr(builder, "_load_replay_module", lambda _repo_root: replay)

    candidate_root = tmp_path / "sdk-candidates"
    builder.build_candidates(
        repo_root=REPO_ROOT,
        xray_candidate_manifest_path=capture_manifest,
        candidate_root=candidate_root,
        surfaces=(surface,),
    )

    packet = json.loads(
        (
            candidate_root
            / "groundx-python"
            / "tests"
            / "extract"
            / "fixtures"
            / "extraction-boundary"
            / "boundary-goldens"
            / surface
            / "groundx_python_xray_reassembly.expected.json"
        ).read_text()
    )
    assert packet == _complete_output_values()
    assert consumed == {
        "handoff_sha256": _sha256(candidate_handoff),
        "xray_sha256": _sha256(candidate_xray),
    }
