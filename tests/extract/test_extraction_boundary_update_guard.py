from pathlib import Path


def test_boundary_replay_cannot_update_approved_goldens() -> None:
    source = (
        Path(__file__).with_name("test_extraction_boundary_reassembly.py").read_text()
    )
    forbidden = "UPDATE_GROUNDX_PYTHON_" + "EXTRACT_BOUNDARY_GOLDENS"

    assert forbidden not in source, (
        "approved fixtures must be updated through the Studio Harness Normal Fixture "
        "Update Path, starting with run_extraction_fixture_seeding.private.py init"
    )
