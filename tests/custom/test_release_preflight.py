from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _test_steps() -> dict[str, dict[str, str]]:
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/ci.yml").read_text())
    return {step["name"]: step for step in workflow["jobs"]["test"]["steps"]}


def test_contributor_guide_is_preserved_during_fern_generation() -> None:
    preserved_paths = {
        line.strip()
        for line in (REPO_ROOT / ".fernignore").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "CONTRIBUTING.md" in preserved_paths


def test_release_preflight_ci_is_preserved_during_fern_generation() -> None:
    preserved_paths = {
        line.strip()
        for line in (REPO_ROOT / ".fernignore").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert ".github/workflows/ci.yml" in preserved_paths


def test_aiohttp_ci_install_retains_extract_dependencies() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text()

    assert "poetry install --extras extract --extras aiohttp" in workflow


def test_ci_runs_one_unmodified_test_suite_for_branches_and_tags() -> None:
    step = _test_steps()["Test"]
    assert "if" not in step
    assert step["run"] == "poetry run pytest -rP -n auto ."


def test_protected_replay_and_fixture_pack_exist() -> None:
    assert (
        REPO_ROOT / "tests/extract/test_compact_fixture_pack_replay.py"
    ).is_file(), "a missing protected replay must block publishing"
    pack_root = REPO_ROOT / "tests/extract/fixtures/extraction-fixture-pack"
    assert (pack_root / "fixture-pack.json").is_file()
    assert (pack_root / "blobs" / "sha256").is_dir()
