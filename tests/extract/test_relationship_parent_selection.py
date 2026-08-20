import pytest

from groundx.extract import RelationshipParentSelection, select_relationship_parent

MATCH_ATTRS = ["meter_number", "provider_name", "service_type"]


def _select(parents, child, **relationship):
    return select_relationship_parent(
        parents,
        child,
        {"match_attrs": MATCH_ATTRS, **relationship},
    )


def test_selects_first_parent_with_same_populated_key_shape() -> None:
    parents = [
        {
            "meter_number": "M-1",
            "provider_name": "Utility",
            "service_type": "water",
        },
        {
            "meter_number": "m-1",
            "provider_name": "utility",
            "service_type": "WATER",
        },
    ]
    child = {
        "meter_number": " M-1 ",
        "provider_name": "Utility",
        "service_type": "water",
    }

    selection = _select(parents, child)

    assert selection == RelationshipParentSelection(parents[0], False)
    assert selection.parent is parents[0]


@pytest.mark.parametrize(
    ("parents", "child"),
    [
        ([{"meter_number": "12"}], {"meter_number": "12"}),
        ([{"meter_number": 12}], {"meter_number": 12.0}),
        ([{"meter_number": {"value": "12"}}], {"meter_number": "12"}),
        (
            [{"meter_number": "12", "provider_name": "", "service_type": None}],
            {"meter_number": "12"},
        ),
    ],
)
def test_matches_equal_populated_values(parents, child) -> None:
    assert _select(parents, child).parent is parents[0]


@pytest.mark.parametrize(
    ("parent_value", "child_value"),
    [
        ("M 1", "M  1"),
        ("12", 12),
        (True, 1),
        ("2026-1-2", "2026-01-02"),
    ],
)
def test_does_not_normalize_distinct_values(parent_value, child_value) -> None:
    parent = {"meter_number": parent_value}
    child = {"meter_number": child_value}

    assert _select([parent], child).parent is None


@pytest.mark.parametrize(
    ("parent", "child"),
    [
        (
            {"meter_number": "12", "provider_name": "Utility"},
            {"meter_number": "12"},
        ),
        (
            {"meter_number": "12"},
            {"meter_number": "12", "provider_name": "Utility"},
        ),
        (
            {"meter_number": "12", "service_type": "water"},
            {"meter_number": "12", "service_type": "electric"},
        ),
    ],
)
def test_requires_equal_populated_key_shape_and_values(parent, child) -> None:
    assert _select([parent], child).parent is None


def test_ignores_passthrough_fallback_metadata() -> None:
    parent = {
        "meter_number": "12",
        "provider_name": "Utility",
        "service_type": "water",
    }
    child = {
        "meter_number": "12",
        "provider_name": "Other Utility",
        "service_type": "water",
    }

    selection = _select(
        [parent],
        child,
        parent_passthrough_attrs=["provider_name"],
    )

    assert selection == RelationshipParentSelection(None, False)


def test_ignores_tie_strategy_metadata() -> None:
    parents = [
        {"meter_number": "M-1"},
        {"meter_number": "m-1"},
    ]

    selection = _select(
        parents,
        {"meter_number": "M-1"},
        multiple_match_strategy="unsupported",
    )

    assert selection == RelationshipParentSelection(parents[0], False)


def test_accepts_dispatched_match_attrs() -> None:
    parent = {"meter_number": "12"}

    selection = select_relationship_parent(
        [parent],
        {"meter_number": "12"},
        {"matchAttrs": ["meter_number"]},
    )

    assert selection.parent is parent


@pytest.mark.parametrize(
    ("parents", "child", "relationship"),
    [
        ([], {"meter_number": "12"}, {"match_attrs": ["meter_number"]}),
        ([{"meter_number": "12"}], {}, {"match_attrs": ["meter_number"]}),
        ([{"meter_number": "12"}], {"meter_number": "12"}, {}),
        ([{"meter_number": "12"}], {"meter_number": "12"}, {"match_attrs": []}),
        ([{"meter_number": object()}], {"meter_number": object()}, {"match_attrs": ["meter_number"]}),
    ],
)
def test_no_match_is_total_and_not_ambiguous(parents, child, relationship) -> None:
    assert select_relationship_parent(parents, child, relationship) == RelationshipParentSelection(None, False)
