import hashlib
import json
import shutil
import subprocess
import sys
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
                }
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
    assert json.loads(candidate_expected.read_text()) == json.loads(accepted_expected.read_text())
    assert json.loads(candidate_diff.read_text())["changes"] == []
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
