import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tests" / "extract" / "build_extraction_boundary_candidates.py"
SURFACE = "arcadia_legacy"
BOUNDARY_ROOT = REPO_ROOT / "tests" / "extract" / "fixtures" / "extraction-boundary"


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


def _proposed_handoff_candidate(root: Path, surface: str) -> dict[str, object]:
    relative = Path(
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        f"inputs/{surface}/internal_arcadia_download_workflow_load.handoff.json"
    )
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        BOUNDARY_ROOT / "inputs" / surface / "internal_arcadia_download_workflow_load.handoff.json",
        target,
    )
    return {
        "surface": surface,
        "artifact_name": "internal_arcadia_download_workflow_load",
        "candidate_path": "internal-arcadia-agents/expected.json",
        "sha256": "d" * 64,
        "next_boundary_inputs": [
            {
                "candidate_path": str(relative),
                "sha256": _sha256(target),
            }
        ],
    }


def test_builder_default_surfaces_follow_projection_order(monkeypatch) -> None:
    projection = {"cases": [{"surface": "third"}, {"surface": "first"}]}
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
    accepted_sidecar = BOUNDARY_ROOT / "inputs" / SURFACE / "groundx_python_xray_reassembly.xray.json"
    accepted_expected = BOUNDARY_ROOT / "boundary-goldens" / SURFACE / "groundx_python_xray_reassembly.expected.json"
    accepted_hashes = {
        accepted_sidecar: _sha256(accepted_sidecar),
        accepted_expected: _sha256(accepted_expected),
    }

    sidecar_root = tmp_path / "sidecars"
    relative_sidecar = Path(
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        f"inputs/{SURFACE}/groundx_python_xray_reassembly.xray.json"
    )
    candidate_sidecar = sidecar_root / relative_sidecar
    candidate_sidecar.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(accepted_sidecar, candidate_sidecar)
    sidecar_manifest = sidecar_root / "fixture_candidate_manifest.json"
    _write_json(
        sidecar_manifest,
        {
            "schema_version": "extraction_boundary_fixture_candidate_v1",
            "status": "pending_review",
            "run_id": "live-20260726T132601Z-test",
            "run_mode": "fixture_seeding",
            "artifact_catalog_version": "2026-07-23.1",
            "artifact_catalog_sha256": "a" * 64,
            "source_boundary_manifest_sha256": "b" * 64,
            "candidates": [
                {
                    "surface": SURFACE,
                    "artifact_name": ("groundx_python_xray_reassembly_xray_sidecar"),
                    "candidate_path": str(relative_sidecar),
                    "sha256": _sha256(candidate_sidecar),
                    "source_sha256": "c" * 64,
                    "source_hosted_path": ("layout/processed/task/document-xray.json"),
                },
                _proposed_handoff_candidate(sidecar_root, SURFACE),
            ],
        },
    )

    candidate_root = tmp_path / "sdk-candidates"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--xray-candidate-manifest",
            str(sidecar_manifest),
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
    assert candidate_review["current_accepted_sha256"] == _sha256(accepted_expected)
    assert isinstance(candidate_review["changes"], list)
    assert {path: _sha256(path) for path in accepted_hashes} == accepted_hashes

    candidate_sidecar.write_text("{}\n")
    mismatch = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--xray-candidate-manifest",
            str(sidecar_manifest),
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
    assert "X-Ray candidate hash does not match" in mismatch.stderr


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


def test_builder_records_reassembly_when_quality_assertions_fail(
    tmp_path: Path,
    monkeypatch,
) -> None:
    surface = "adp_v1"
    accepted_sidecar = BOUNDARY_ROOT / "inputs" / surface / "groundx_python_xray_reassembly.xray.json"
    sidecar_root = tmp_path / "sidecars"
    relative_sidecar = Path(
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        f"inputs/{surface}/groundx_python_xray_reassembly.xray.json"
    )
    candidate_sidecar = sidecar_root / relative_sidecar
    candidate_sidecar.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(accepted_sidecar, candidate_sidecar)
    sidecar_manifest = sidecar_root / "fixture_candidate_manifest.json"
    _write_json(
        sidecar_manifest,
        {
            "schema_version": "extraction_boundary_fixture_candidate_v1",
            "status": "pending_review",
            "run_id": "live-20260727T175600Z-test",
            "run_mode": "fixture_seeding",
            "artifact_catalog_version": "2026-07-23.1",
            "artifact_catalog_sha256": "a" * 64,
            "source_boundary_manifest_sha256": "b" * 64,
            "candidates": [
                {
                    "surface": surface,
                    "artifact_name": ("groundx_python_xray_reassembly_xray_sidecar"),
                    "candidate_path": str(relative_sidecar),
                    "sha256": _sha256(candidate_sidecar),
                    "source_sha256": "c" * 64,
                    "source_hosted_path": ("layout/processed/task/document-xray.json"),
                },
                _proposed_handoff_candidate(sidecar_root, surface),
            ],
        },
    )
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
        xray_candidate_manifest_path=sidecar_manifest,
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
    sidecar_root = tmp_path / "provider-candidates"
    relative_sidecar = Path(
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        f"inputs/{surface}/groundx_python_xray_reassembly.xray.json"
    )
    relative_handoff = Path(
        "groundx-python/tests/extract/fixtures/extraction-boundary/"
        f"inputs/{surface}/internal_arcadia_download_workflow_load.handoff.json"
    )
    candidate_sidecar = sidecar_root / relative_sidecar
    candidate_handoff = sidecar_root / relative_handoff
    _write_json(candidate_sidecar, {"xray": {"source": "proposed"}})
    _write_json(candidate_handoff, {"request": {"source": "proposed"}})
    sidecar_manifest = sidecar_root / "fixture_candidate_manifest.json"
    _write_json(
        sidecar_manifest,
        {
            "schema_version": "extraction_boundary_fixture_candidate_v1",
            "status": "pending_review",
            "run_id": "live-20260810T164000Z-test",
            "run_mode": "fixture_capture",
            "artifact_catalog_version": "2026-07-23.1",
            "artifact_catalog_sha256": "a" * 64,
            "source_boundary_manifest_sha256": "b" * 64,
            "candidates": [
                {
                    "surface": surface,
                    "artifact_name": "groundx_python_xray_reassembly_xray_sidecar",
                    "candidate_path": str(relative_sidecar),
                    "sha256": _sha256(candidate_sidecar),
                    "source_sha256": "c" * 64,
                    "source_hosted_path": "layout/processed/task/document-xray.json",
                },
                {
                    "surface": surface,
                    "artifact_name": "internal_arcadia_download_workflow_load",
                    "candidate_path": "internal-arcadia-agents/expected.json",
                    "sha256": "d" * 64,
                    "next_boundary_inputs": [
                        {
                            "candidate_path": str(relative_handoff),
                            "sha256": _sha256(candidate_handoff),
                        }
                    ],
                },
            ],
        },
    )
    accepted_output = tmp_path / "accepted.json"
    _write_json(accepted_output, {"input_sha256": "accepted"})
    replay = types.SimpleNamespace()

    def build_candidate(_candidate_root: Path, selected_surface: str):
        producer_path = replay._real_download_workflow_load_input_path(selected_surface)
        xray_path = replay._real_xray_sidecar_path(selected_surface)
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
        xray_candidate_manifest_path=sidecar_manifest,
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
    assert packet["xray_sha256"] == _sha256(candidate_sidecar)
