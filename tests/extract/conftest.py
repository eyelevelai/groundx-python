"""Draft-only marker registration for the task 3.2a7b RED test files.

Registers the two provenance markers used by
`test_relationship_parent_selection_red.py` and
`test_relationship_parent_selection_seam_red.py` so that a reader can select or
exclude rows whose target behavior is not yet ratified:

    pytest -m "not pending_decision"

This file registers marker names only.  It changes no behavior and adds no
fixtures.
"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "pending_decision: target behavior is unresolved; the assertion is NOT a "
        "ratified target and is on the plan-owner question list",
    )
    # RULING 7a (2026-08-05) adopted current-head matcher semantics, so no row
    # carries this marker any more.  It stays registered so the documented slice
    # commands keep working and so a future unratified row has a home.
    config.addinivalue_line(
        "markers",
        "pending_authorization: behavior taken from a revision the plan does not "
        "name; needs plan-owner ratification (currently unused -- see RULING 7a)",
    )
    config.addinivalue_line(
        "markers",
        "pending_fixture_promotion: accepted fixture assertion remains intentionally "
        "red until the guarded post-deployment promotion removes this marker",
    )
