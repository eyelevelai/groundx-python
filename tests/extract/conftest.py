"""Draft-only marker registration for the task 3.2a7b RED test files.

Registers the two provenance markers used by
`test_relationship_parent_selection_red.py` and
`test_relationship_parent_selection_seam_red.py` so that a reader can select or
exclude rows whose target behavior is not yet ratified:

    pytest -m "not pending_decision and not pending_authorization"

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
    config.addinivalue_line(
        "markers",
        "pending_authorization: behavior taken from Internal Arcadia main @2797b5e, "
        "a revision tasks.md:1358-1360 does not name; needs plan-owner ratification",
    )
