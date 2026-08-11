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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _coherent_candidate_manifest(
    root: Path,
    surface: str,
    *,
    xray: object | None = None,
    handoff: dict[str, object] | None = None,
) -> tuple[Path, dict[str, object], Path, Path]:
    xray_entry, xray_path = _proposed_xray_candidate(root, surface, xray=xray)
    handoff_entry, handoff_path = _proposed_handoff_candidate(
        root,
        surface,
        packet=handoff,
    )
    manifest: dict[str, object] = {
        "schema_version": "extraction_boundary_fixture_candidate_v1",
        "status": "pending_review",
        "run_id": RUN_ID,
        "run_mode": RUN_MODE,
        "artifact_catalog_version": "2026-07-23.1",
        "artifact_catalog_sha256": "a" * 64,
        "source_boundary_manifest_sha256": BOUNDARY_MANIFEST_SHA256,
        "candidates": [xray_entry, handoff_entry],
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


def test_builder_writes_review_candidates_without_touching_accepted_fixtures(
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

    assert result.returncode == 0, result.stderr
    manifest = json.loads((candidate_root / "fixture_candidate_manifest.json").read_text())
    assert len(manifest["candidates"]) == 1
    assert set(manifest["generator"]) == {
        "boundary_replay_sha256",
        "candidate_builder_sha256",
        "production_reassembly_sha256",
    }
    assert all(len(value) == 64 for value in manifest["generator"].values())
    candidate = manifest["candidates"][0]
    assert candidate["artifact_name"] == "groundx_python_xray_reassembly"
    assert candidate["surface"] == SURFACE
    candidate_expected = candidate_root / candidate["candidate_path"]
    candidate_diff = candidate_root / candidate["candidate_diff_path"]
    candidate_packet = json.loads(candidate_expected.read_text())
    candidate_review = json.loads(candidate_diff.read_text())
    assert candidate_packet["surface"] == SURFACE
    assert candidate_review["status"] == "pending_review"
    assert candidate_review["candidate_sha256"] == _sha256(candidate_expected)
    assert candidate_review["current_accepted_sha256"] is None
    assert isinstance(candidate_review["changes"], list)

    candidate_xray.write_text("{}\n")
    mismatch = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--xray-candidate-manifest",
            str(capture_manifest),
            "--candidate-root",
            str(tmp_path / "mismatch-candidates"),
            "--surfaces",
            SURFACE,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )
    assert mismatch.returncode != 0
    assert "X-Ray predecessor hash does not match" in mismatch.stderr


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
    capture_manifest, _manifest, _xray_path, _handoff_path = _coherent_candidate_manifest(capture_root, surface)
    accepted_output = tmp_path / "accepted.json"
    _write_json(
        accepted_output,
        {
            "assertions": {"shape_contract_passed": True},
            "shape_assertions": {"has_adp_core_fields_populated_by_section": True},
        },
    )
    actual = {
        "assertions": {"shape_contract_passed": False},
        "shape_assertions": {"has_adp_core_fields_populated_by_section": False},
    }
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
    assert candidate["assertions"]["shape_contract_passed"] is False
    assert candidate["shape_assertions"]["has_adp_core_fields_populated_by_section"] is False


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
    )
    accepted_output = tmp_path / "accepted.json"
    _write_json(accepted_output, {"input_sha256": "accepted"})
    replay = types.SimpleNamespace()

    def build_candidate(_candidate_root: Path, selected_surface: str):
        producer_path = replay._real_download_workflow_load_input_path(selected_surface)
        xray_path = replay._real_xray_predecessor_path(selected_surface)
        return (
            {
                "input_sha256": _sha256(producer_path),
                "xray_sha256": _sha256(xray_path),
            },
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
    assert packet["input_sha256"] == _sha256(candidate_handoff)
    assert packet["xray_sha256"] == _sha256(candidate_xray)
