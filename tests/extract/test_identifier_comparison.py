import pytest

from groundx.extract import match_key, select_relationship_parent, values_match
from groundx.extract.custom_outputs import _dedupe_repeated_records


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("Meter OIB", "meter018"),
        ("A\tB\nC", "a8c"),
        ("I L 1", "111"),
        ("Straße", "STRASSE"),
        ("A\u00a0B", "a8"),
    ],
)
def test_match_key_ignores_only_approved_extraction_noise(left: str, right: str) -> None:
    assert match_key(left) == match_key(right)
    assert values_match(left, right)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("AB-12", "AB12"),
        ("S", "5"),
        ("Z", "2"),
        ("AB1", "AB11"),
    ],
)
def test_match_key_preserves_unapproved_differences(left: str, right: str) -> None:
    assert match_key(left) != match_key(right)
    assert not values_match(left, right)


@pytest.mark.parametrize("value", [None, 1, True, [], {}])
def test_match_helpers_reject_nonstrings(value: object) -> None:
    with pytest.raises(TypeError):
        match_key(value)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        values_match(value, "1")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        values_match("1", value)  # type: ignore[arg-type]


def test_relationship_parent_selection_uses_shared_string_match_without_rewriting() -> None:
    first = {"meter_id": "M-OIB"}
    second = {"meter_id": "M-019"}

    selection = select_relationship_parent(
        [first, second],
        {"meter_id": " m-o 1 8 "},
        {"match_attrs": ["meter_id"]},
    )

    assert selection.parent is first
    assert selection.parent["meter_id"] == "M-OIB"


def test_repeated_identity_uses_shared_match_even_when_exact_attrs_are_present() -> None:
    first = {"meter_id": " M-OIB ", "label": "first"}
    second = {"meter_id": "m-018", "description": "second"}

    deduped = _dedupe_repeated_records(
        [first, second],
        ["meter_id"],
        {
            "exact_attrs": ["meter_id"],
            "threshold_attrs": [],
            "activate_threshold_at": 0,
            "minimum_threshold_matches": 0,
        },
    )

    assert deduped == [
        {
            "meter_id": " M-OIB ",
            "label": "first",
            "description": "second",
        }
    ]
