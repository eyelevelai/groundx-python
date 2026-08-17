from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("openspec/specs/extraction-placement/spec.md")
CONSOLIDATED_ROUTE = (
    "internal-arcadia-agents/openspec/changes/complete-extraction-boundary-regression-coverage/tasks.md"
)
STALE_ROUTE = "2026-07-10-bound-workflow-cache-loads"


def test_agents_routes_to_extraction_placement_contract() -> None:
    agents = (REPO_ROOT / "AGENTS.md").read_text()

    assert f"]({CONTRACT_PATH.as_posix()})" in agents


def test_extraction_placement_contract_pins_sdk_ownership() -> None:
    contract = " ".join((REPO_ROOT / CONTRACT_PATH).read_text().split())

    required_text = (
        "GroundX Python SHALL own its hand-written extraction YAML parser/compiler",
        "GroundX Python SHALL also own production X-Ray/custom-output reassembly",
        "`role` SHALL select processing and relationship direction",
        "`output_scope` SHALL select authored placement",
        "Each `final_path` SHALL be the complete destination tree",
        "Path depth SHALL never determine output scope",
    )

    for text in required_text:
        assert text in contract


def test_active_openspec_changes_route_to_consolidated_plan() -> None:
    # Extraction-project scaffolding: dies with the consolidated plan's
    # archive (its task 10.5). An empty changes directory is legal.
    changes_root = REPO_ROOT / "openspec/changes"
    active_changes = sorted(path for path in changes_root.iterdir() if path.is_dir() and path.name != "archive")

    for change in active_changes:
        body = "\n".join(path.read_text() for path in sorted(change.rglob("*.md")))
        assert CONSOLIDATED_ROUTE in body, (
            f"{change.relative_to(REPO_ROOT)} must route remaining work to "
            "complete-extraction-boundary-regression-coverage"
        )
        assert STALE_ROUTE not in body, f"{change.relative_to(REPO_ROOT)} retains the stale plan route {STALE_ROUTE}"
