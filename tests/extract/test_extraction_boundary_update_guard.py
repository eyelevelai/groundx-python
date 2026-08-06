from pathlib import Path


def test_boundary_replay_cannot_update_approved_goldens() -> None:
    source = (
        Path(__file__).with_name("test_extraction_boundary_reassembly.py").read_text()
    )
    forbidden = "UPDATE_GROUNDX_PYTHON_" + "EXTRACT_BOUNDARY_GOLDENS"

    assert forbidden not in source, (
        "approved fixtures must be updated through the reviewed Harness promotion flow"
    )


def test_boundary_fixture_guide_limits_intentional_reassembly_changes() -> None:
    guide = (
        Path(__file__).parent / "fixtures" / "extraction-boundary" / "README.md"
    ).read_text()

    required = [
        "intentional reassembly change",
        "declared output differences",
        "Every undeclared difference remains a regression",
        "old fixture remains the before-state",
        "Current SDK output cannot approve itself",
    ]
    for phrase in required:
        assert phrase in guide
