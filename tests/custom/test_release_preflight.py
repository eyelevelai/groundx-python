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
    assert "scripts/verify_release_intentional_red.py" in preserved_paths


def test_aiohttp_ci_install_retains_extract_dependencies() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text()

    assert "poetry install --extras extract --extras aiohttp" in workflow


def test_pull_request_ci_keeps_intentional_fixture_failures_active() -> None:
    step = _test_steps()["Test pre-promotion code"]

    assert step["if"] == "${{ !startsWith(github.ref, 'refs/tags/') }}"
    assert step["run"] == (
        'poetry run pytest -rP -n auto -m "not pending_decision and not pending_fixture_promotion" .'
    )


def test_tag_release_uses_exact_intentional_red_classifier() -> None:
    steps = _test_steps()
    source_step = steps["Test release source"]
    classifier_step = steps["Verify exact intentional fixture outcomes"]

    assert source_step["if"] == "${{ startsWith(github.ref, 'refs/tags/') }}"
    assert source_step["run"] == (
        'poetry run pytest -rP -n auto -m "not pending_decision and not pending_fixture_promotion '
        'and not release_intentional_fixture_red" .'
    )
    assert classifier_step["if"] == "${{ startsWith(github.ref, 'refs/tags/') }}"
    assert "-m release_intentional_fixture_red" in classifier_step["run"]
    assert "verify_release_intentional_red.py" in classifier_step["run"]
    assert 'case "$status" in' in classifier_step["run"]
    assert "0|1)" in classifier_step["run"]


def test_release_handoff_documents_the_intentional_fixture_gate() -> None:
    guide = " ".join((REPO_ROOT / "CONTRIBUTING.md").read_text().split())

    assert "Ordinary pull-request CI keeps these protected tests failing" in guide
    assert "exactly seven approved missing-fixture failures" in guide
    assert "all seven tests pass after fixture promotion" in guide
