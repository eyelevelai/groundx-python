from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


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
