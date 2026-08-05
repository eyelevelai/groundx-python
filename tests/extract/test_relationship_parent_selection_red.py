"""RED tests for task 3.2a7b: the one exported parent-selection primitive.

These tests are written BEFORE the implementation and are expected to FAIL.
They encode the charge-to-meter parent-selection behavior table recovered from
Internal Arcadia source history, expressed against the generic SDK contract.

Legacy source of truth (repo checkout `/private/tmp/codex-internal-merge-20260803`):

* implementation: `classes/statement.py::Statement.get_charge_meter`
  - `main` @ `2797b5e` lines 3776-3850 (current, authoritative)
  - `24a490c` lines 3105-3179 == `d4f8ead` lines 2917-2991 (byte identical)
  - `0c359e45` lines 2679-2710 (pre-fallback baseline, superseded)
* tests: `classes/test_statement.py`
  - `main` @ `2797b5e`: `test_get_charge_meter` 5619-5701,
    `test_get_charge_meter_uses_stable_first_exact_match` 5703-5744,
    `test_get_charge_meter_matches_reviewed_available_identity` 5746-5844
  - `0c359e45`: `test_get_charge_meter` 3477-3517
* policy: `prompts/yaml.py` lines 98-102 (`charge_match_attrs`) and 162-167
  (`meter_passthrough_attrs`); `prompts/extraction_policy.py` lines 365-377
* value comparison: `groundx/extract/classes/field.py` lines 76-90
  (`ExtractedField.equal_to_value`, case-insensitive)
* emptiness: `classes/image_evidence.py` lines 273-285 (`is_empty_source_value`)
* contract: `openspec/changes/complete-extraction-boundary-regression-coverage/`
  `tasks.md` 1355-1378 (3.2a7b), 1379-1400 (3.2a7c), `design.md` 380-430,
  `specs/extraction-boundary-regression/spec.md` 335-375

CONTRACT PINNED BY THESE TESTS
------------------------------
`groundx.extract` exports exactly one parent-selection primitive.  The name
`select_relationship_parent` is this lane's proposal; if the implementer picks
another name, rename it in `_MATCHER_NAME` below only.

Signature::

    select_relationship_parent(parents, child, relationship) -> selection

`parents` is an ordered sequence of parent records, `child` is one child
record, `relationship` is the seven-field relationship packet in either the
persisted snake_case or the dispatched camelCase spelling.

The return value must express two things: which parent was selected (or that
none was) and whether the outcome was blocked by declared ambiguity.  Both a
result object exposing `.parent` / `.ambiguous` and a bare parent-or-None
return are accepted by `_selection` below; ambiguity assertions require the
object form.
"""

import typing

import pytest

import groundx.extract as extract

_MATCHER_NAME = "select_relationship_parent"

_ABSENT = object()
_MISSING = object()

# Logical match-field roles used by the behavior table.  "M" and "S" are stable
# identity fields; "P" is the field the parent group also names in its
# `passthrough_attrs`, so it is the only field the source-history fallback may
# remove from comparison.
_M = "M"
_P = "P"
_S = "S"


class _Naming(typing.NamedTuple):
    label: str
    parent_group: str
    child_group: str
    parent_output_field: str
    unmatched_child_group: str
    m: str
    p: str
    s: str
    extra_passthrough: typing.Tuple[str, ...]


# Names taken verbatim from the accepted boundary inputs:
# tests/extract/fixtures/extraction-boundary/inputs/{arcadia_legacy,arcadia_v1,
# generic_v1}/internal_arcadia_download_workflow_load.handoff.json
ARCADIA = _Naming(
    label="arcadia",
    parent_group="meters",
    child_group="charges",
    parent_output_field="meter_charges",
    unmatched_child_group="account_charges",
    m="meter_number",
    p="provider_name",
    s="service_type",
    extra_passthrough=(
        "deregulation_status",
        "pass_through_provider_account_number",
        "pass_through_provider_name",
    ),
)
GENERIC = _Naming(
    label="generic_v1",
    parent_group="generic_group_b",
    child_group="generic_group_c",
    parent_output_field="generic_group_c",
    unmatched_child_group="generic_group_c",
    m="generic_attr_18",
    p="generic_attr_08",
    s="generic_attr_23",
    extra_passthrough=(
        "generic_attr_15",
        "generic_attr_19",
        "generic_attr_20",
    ),
)
NAMINGS = (ARCADIA, GENERIC)


class Row(typing.NamedTuple):
    row_id: str
    parents: typing.Tuple[typing.Mapping[str, typing.Any], ...]
    child: typing.Mapping[str, typing.Any]
    expected_index: typing.Optional[int]
    stage: str  # "exact" | "fallback" | "none"
    ambiguous: bool
    strategy: typing.Optional[str]
    cite: str


def _row(
    row_id: str,
    parents: typing.Sequence[typing.Mapping[str, typing.Any]],
    child: typing.Mapping[str, typing.Any],
    expected_index: typing.Optional[int],
    stage: str,
    cite: str,
    *,
    ambiguous: bool = False,
    strategy: typing.Optional[str] = None,
) -> Row:
    return Row(
        row_id=row_id,
        parents=tuple(parents),
        child=child,
        expected_index=expected_index,
        stage=stage,
        ambiguous=ambiguous,
        strategy=strategy,
        cite=cite,
    )


_P0 = {_M: "12", _P: "Test", _S: "water"}
_P0_CONFLICTED = {_M: "12", _P: "Test", _S: "water", "P__conflicts": ["Other"]}
_STMT = "internal-arcadia classes/test_statement.py@2797b5e"
_IMPL = "internal-arcadia classes/statement.py@2797b5e"

BEHAVIOR_TABLE: typing.Tuple[Row, ...] = (
    # --- single complete parent, every supplied-identity combination -------
    _row("R01_no_identity", [_P0], {}, None, "none", f"{_STMT}:5638-5639; {_IMPL}:3791-3792"),
    _row("R02_stable_m_only", [_P0], {_M: "12"}, None, "none", f"{_STMT}:5641-5642; {_IMPL}:3794-3797"),
    _row("R03_passthrough_only", [_P0], {_P: "Test"}, None, "none", f"{_STMT}:5643-5644"),
    _row("R04_stable_s_only", [_P0], {_S: "water"}, None, "none", f"{_STMT}:5645-5646"),
    _row("R05_both_stable_fields", [_P0], {_M: "12", _S: "water"}, 0, "fallback", f"{_STMT}:5647-5648; {_IMPL}:3821-3850"),
    _row("R06_passthrough_and_one_stable", [_P0], {_P: "Test", _S: "water"}, None, "none", f"{_STMT}:5649-5650"),
    _row("R07_other_passthrough_and_stable", [_P0], {_M: "12", _P: "Test"}, None, "none", f"{_STMT}:5651-5652"),
    _row("R08_exact_full_identity", [_P0], dict(_P0), 0, "exact", f"{_STMT}:5653-5656; {_IMPL}:3805-3819"),
    _row("R09_wrong_stable_value", [_P0], {_M: "123", _P: "Test", _S: "water"}, None, "none", f"{_STMT}:5657-5660"),
    _row("R10_differing_passthrough_value", [_P0], {_M: "12", _P: "Test Utility", _S: "water"}, 0, "fallback", f"{_STMT}:5661-5668; {_IMPL}:3821-3850"),
    # --- conflicting ignored (passthrough) field blocks the fallback -------
    _row("R11_conflicted_ignored_field_unknown_value", [_P0_CONFLICTED], {_M: "12", _P: "Unknown", _S: "water"}, None, "none", f"{_STMT}:5686-5693; {_IMPL}:3836-3841"),
    _row("R12_conflicted_ignored_field_rival_value", [_P0_CONFLICTED], {_M: "12", _P: "Other", _S: "water"}, None, "none", f"{_STMT}:5694-5701; {_IMPL}:3836-3841"),
    # --- two parents sharing the stable identity --------------------------
    _row(
        "R13_two_fallback_candidates_are_not_unique",
        [_P0, {_M: "12", _P: "Other", _S: "water"}],
        {_M: "12", _P: "Unknown", _S: "water"},
        None,
        "none",
        f"{_IMPL}:3843-3850 (unique-candidate requirement); prep report row 3",
    ),
    _row(
        "R14_exact_wins_over_ambiguous_fallback",
        [_P0, {_M: "12", _P: "Other", _S: "water"}],
        {_M: "12", _P: "Other", _S: "water"},
        1,
        "exact",
        f"{_IMPL}:3805-3819 (algorithm-derived: exact pass precedes fallback; the legacy "
        f"two-meter input at {_STMT}:5670-5701 collapses to one record via add_meter conflict merge)",
    ),
    # --- more than one exact candidate: declared strategy only ------------
    _row(
        "R15_multiple_exact_first_stable",
        [{_M: "M-1", _P: "Utility", _S: "water"}, {_M: "m-1", _P: "utility", _S: "WATER"}],
        {_M: "M-1", _P: "Utility", _S: "water"},
        0,
        "exact",
        f"{_STMT}:5721-5744; {_IMPL}:3818-3819; groundx/extract/classes/field.py:85-90",
        strategy="first_stable",
    ),
    _row(
        "R16_multiple_exact_without_strategy_is_ambiguous",
        [{_M: "M-1", _P: "Utility", _S: "water"}, {_M: "m-1", _P: "utility", _S: "WATER"}],
        {_M: "M-1", _P: "Utility", _S: "water"},
        None,
        "none",
        "DELIBERATE DIVERGENCE from legacy assertion "
        f"{_STMT}:5741 (which returns the first candidate unconditionally). "
        "openspec tasks.md:1366-1367 'Ambiguity follows only the packet's declared "
        "strategy' and tasks.md:1381-1382 'Delete the unconditional direct_matches[0] result'.",
        ambiguous=True,
    ),
    # --- reviewed available-identity matrix -------------------------------
    _row("R17_exact_full_match", [{_M: "M-1", _P: "Utility", _S: "water"}], {_M: "M-1", _P: "Utility", _S: "water"}, 0, "exact", f"{_STMT}:5754-5759"),
    _row("R18_passthrough_mismatch_unique_stable", [{_M: "M-1", _P: "Utility", _S: "water"}], {_M: "M-1", _P: "Other Utility", _S: "water"}, 0, "fallback", f"{_STMT}:5760-5773"),
    _row("R19_missing_child_side", [{_M: "M-1", _P: "Utility", _S: "water"}], {_M: "M-1", _S: "water"}, 0, "fallback", f"{_STMT}:5774-5783"),
    _row("R20_missing_parent_side", [{_M: "M-1", _S: "water"}], {_M: "M-1", _P: "Utility", _S: "water"}, 0, "fallback", f"{_STMT}:5784-5793"),
    _row("R21_missing_both_sides", [{_M: "M-1", _S: "water"}], {_M: "M-1", _S: "water"}, 0, "exact", f"{_STMT}:5794-5799"),
    # --- empty passthrough values are absent, not mismatching -------------
    _row("R22a_none_child_side", [{_M: "M-1", _P: "Utility", _S: "water"}], {_M: "M-1", _P: None, _S: "water"}, 0, "fallback", f"{_STMT}:5801-5830; image_evidence.py:273-277"),
    _row("R22b_blank_child_side", [{_M: "M-1", _P: "Utility", _S: "water"}], {_M: "M-1", _P: "", _S: "water"}, 0, "fallback", f"{_STMT}:5801-5830; image_evidence.py:273-277"),
    _row("R22c_whitespace_child_side", [{_M: "M-1", _P: "Utility", _S: "water"}], {_M: "M-1", _P: "   ", _S: "water"}, 0, "fallback", f"{_STMT}:5801-5830; image_evidence.py:273-277"),
    _row("R23a_none_parent_side", [{_M: "M-1", _P: None, _S: "water"}], {_M: "M-1", _P: "Utility", _S: "water"}, 0, "fallback", f"{_STMT}:5801-5830"),
    _row("R23b_blank_parent_side", [{_M: "M-1", _P: "", _S: "water"}], {_M: "M-1", _P: "Utility", _S: "water"}, 0, "fallback", f"{_STMT}:5801-5830"),
    _row("R23c_whitespace_parent_side", [{_M: "M-1", _P: "   ", _S: "water"}], {_M: "M-1", _P: "Utility", _S: "water"}, 0, "fallback", f"{_STMT}:5801-5830"),
    _row("R24a_none_both_sides", [{_M: "M-1", _P: None, _S: "water"}], {_M: "M-1", _P: None, _S: "water"}, 0, "exact", f"{_STMT}:5801-5830"),
    _row("R24b_blank_both_sides", [{_M: "M-1", _P: "", _S: "water"}], {_M: "M-1", _P: "", _S: "water"}, 0, "exact", f"{_STMT}:5801-5830"),
    _row("R24c_whitespace_both_sides", [{_M: "M-1", _P: "   ", _S: "water"}], {_M: "M-1", _P: "   ", _S: "water"}, 0, "exact", f"{_STMT}:5801-5830"),
    # --- comparison normalization ----------------------------------------
    _row("R25_case_and_whitespace_tolerant_equality", [{_M: " 12 ", _P: "TEST", _S: "Water"}], {_M: "12", _P: "test", _S: "water"}, 0, "exact", "groundx/extract/classes/field.py:76-90; groundx/extract/custom_outputs.py:1703-1706"),
    # --- conflict handling is scoped to the ignored fields only -----------
    _row("R26_conflict_on_stable_field_does_not_block", [{_M: "12", _P: "Test", _S: "water", "M__conflicts": ["13"]}], {_M: "12", _S: "water"}, 0, "fallback", f"{_IMPL}:3830-3841 (only ignored_match_attrs are conflict-checked)"),
    _row("R27_empty_conflicts_list_does_not_block", [{_M: "12", _P: "Test", _S: "water", "P__conflicts": []}], {_M: "12", _S: "water"}, 0, "fallback", f"{_IMPL}:3839 (truthiness of Field.conflicts)"),
)

_FALLBACK_ROWS = tuple(row for row in BEHAVIOR_TABLE if row.stage == "fallback")


def _matcher() -> typing.Any:
    matcher = getattr(extract, _MATCHER_NAME, None)
    if matcher is None:
        raise AssertionError(
            f"task 3.2a7b contract: groundx.extract must export exactly one "
            f"parent-selection primitive named {_MATCHER_NAME!r}; it is absent"
        )
    return matcher


def _render(
    record: typing.Mapping[str, typing.Any],
    naming: _Naming,
) -> typing.Dict[str, typing.Any]:
    field_for = {_M: naming.m, _P: naming.p, _S: naming.s}
    rendered: typing.Dict[str, typing.Any] = {}
    for key, value in record.items():
        if key.endswith("__conflicts"):
            rendered[f"{field_for[key[: -len('__conflicts')]]}__conflicts"] = value
            continue
        if value is _ABSENT:
            continue
        rendered[field_for[key]] = value
    return rendered


def _packet(
    naming: _Naming,
    *,
    strategy: typing.Optional[str] = None,
    parent_passthrough_attrs: typing.Optional[typing.Sequence[str]] = None,
    match_attrs: typing.Optional[typing.Sequence[str]] = None,
    camel: bool = False,
    parent_output_field: typing.Optional[str] = None,
    unmatched_child_group: typing.Optional[str] = None,
) -> typing.Dict[str, typing.Any]:
    if parent_passthrough_attrs is None:
        parent_passthrough_attrs = (naming.p,) + naming.extra_passthrough
    if match_attrs is None:
        match_attrs = (naming.m, naming.p, naming.s)
    snake = {
        "parent_group": naming.parent_group,
        "child_group": naming.child_group,
        "parent_output_field": parent_output_field or naming.parent_output_field,
        "match_attrs": list(match_attrs),
        "parent_passthrough_attrs": list(parent_passthrough_attrs),
        "unmatched_child_group": unmatched_child_group or naming.unmatched_child_group,
    }
    if strategy is not None:
        snake["multiple_match_strategy"] = strategy
    if not camel:
        return snake
    camel_keys = {
        "parent_group": "parentGroup",
        "child_group": "childGroup",
        "parent_output_field": "parentOutputField",
        "match_attrs": "matchAttrs",
        "parent_passthrough_attrs": "parentPassthroughAttrs",
        "unmatched_child_group": "unmatchedChildGroup",
        "multiple_match_strategy": "multipleMatchStrategy",
    }
    return {camel_keys[key]: value for key, value in snake.items()}


def _index_of(
    parent: typing.Any,
    parents: typing.Sequence[typing.Mapping[str, typing.Any]],
) -> int:
    for index, candidate in enumerate(parents):
        if candidate is parent:
            return index
    for index, candidate in enumerate(parents):
        if candidate == parent:
            return index
    raise AssertionError(f"selected parent {parent!r} is not one of the supplied parents")


def _selection(
    result: typing.Any,
    parents: typing.Sequence[typing.Mapping[str, typing.Any]],
) -> typing.Tuple[typing.Optional[int], bool]:
    """Normalize the primitive's result to (parent_index_or_None, ambiguous)."""
    if result is None:
        return None, False
    if isinstance(result, typing.Mapping) and "parent" not in result:
        return _index_of(result, parents), False
    parent = getattr(result, "parent", _MISSING)
    if parent is _MISSING and isinstance(result, typing.Mapping):
        parent = result.get("parent")
    if parent is _MISSING:
        raise AssertionError(
            "task 3.2a7b contract: the selection result must expose the selected "
            f"parent as `.parent`; got {result!r}"
        )
    ambiguous_raw = getattr(result, "ambiguous", _MISSING)
    if ambiguous_raw is _MISSING and isinstance(result, typing.Mapping):
        ambiguous_raw = result.get("ambiguous", _MISSING)
    if ambiguous_raw is _MISSING:
        raise AssertionError(
            "task 3.2a7b contract: the selection result must report declared "
            f"ambiguity as `.ambiguous`; got {result!r}"
        )
    ambiguous = bool(ambiguous_raw)
    if parent is None:
        return None, ambiguous
    return _index_of(parent, parents), ambiguous


def test_one_parent_selection_primitive_is_exported() -> None:
    assert _MATCHER_NAME in extract.__all__, (
        "task 3.2a7b contract: the parent-selection primitive must be a declared "
        f"public export of groundx.extract; __all__ lacks {_MATCHER_NAME!r}"
    )
    assert callable(_matcher())


@pytest.mark.parametrize("naming", NAMINGS, ids=[naming.label for naming in NAMINGS])
@pytest.mark.parametrize("row", BEHAVIOR_TABLE, ids=[row.row_id for row in BEHAVIOR_TABLE])
def test_behavior_table(row: Row, naming: _Naming) -> None:
    matcher = _matcher()
    parents = [_render(parent, naming) for parent in row.parents]
    child = _render(row.child, naming)
    packet = _packet(naming, strategy=row.strategy)

    index, ambiguous = _selection(matcher(parents, child, packet), parents)

    assert index == row.expected_index, (
        f"{row.row_id} ({naming.label}) expected parent index "
        f"{row.expected_index} via {row.stage}; cite: {row.cite}"
    )
    assert ambiguous is row.ambiguous, (
        f"{row.row_id} ({naming.label}) expected ambiguous={row.ambiguous}; cite: {row.cite}"
    )


@pytest.mark.parametrize("naming", NAMINGS, ids=[naming.label for naming in NAMINGS])
@pytest.mark.parametrize("row", BEHAVIOR_TABLE, ids=[row.row_id for row in BEHAVIOR_TABLE])
def test_behavior_table_camel_case_packet_parity(row: Row, naming: _Naming) -> None:
    """Dispatched camelCase packets must select exactly what snake_case selects.

    design.md:396-399 -- Cashbot persists `parent_passthrough_attrs` /
    `multiple_match_strategy` and dispatches `parentPassthroughAttrs` /
    `multipleMatchStrategy`.
    """
    matcher = _matcher()
    parents = [_render(parent, naming) for parent in row.parents]
    child = _render(row.child, naming)

    snake = _selection(matcher(parents, child, _packet(naming, strategy=row.strategy)), parents)
    camel = _selection(
        matcher(parents, child, _packet(naming, strategy=row.strategy, camel=True)),
        parents,
    )

    assert camel == snake == (row.expected_index, row.ambiguous), (
        f"{row.row_id} ({naming.label}) camel/snake packet parity; cite: {row.cite}"
    )


@pytest.mark.parametrize("naming", NAMINGS, ids=[naming.label for naming in NAMINGS])
@pytest.mark.parametrize("row", _FALLBACK_ROWS, ids=[row.row_id for row in _FALLBACK_ROWS])
def test_no_fallback_when_parent_declares_no_passthrough_attrs(
    row: Row,
    naming: _Naming,
) -> None:
    """`statement.py@2797b5e:3826-3827` -- if the passthrough removal changes
    nothing, there is no fallback pass at all.  Every fallback-only match must
    become unmatched when the parent group declares no passthrough attrs.
    """
    matcher = _matcher()
    parents = [_render(parent, naming) for parent in row.parents]
    child = _render(row.child, naming)
    packet = _packet(naming, strategy=row.strategy, parent_passthrough_attrs=[])

    index, ambiguous = _selection(matcher(parents, child, packet), parents)

    assert index is None, (
        f"{row.row_id} ({naming.label}) must not match without a declared "
        f"parent passthrough attr; cite: {_IMPL}:3826-3827"
    )
    assert ambiguous is False


@pytest.mark.parametrize("naming", NAMINGS, ids=[naming.label for naming in NAMINGS])
def test_all_match_attrs_passthrough_means_no_fallback(naming: _Naming) -> None:
    """`statement.py@2797b5e:3828-3829` -- an empty stable remainder ends selection."""
    matcher = _matcher()
    parents = [_render(_P0, naming)]
    child = _render({_M: "12", _S: "water"}, naming)
    packet = _packet(
        naming,
        parent_passthrough_attrs=[naming.m, naming.p, naming.s],
    )

    index, _ = _selection(matcher(parents, child, packet), parents)

    assert index is None, f"cite: {_IMPL}:3828-3829"


@pytest.mark.parametrize("naming", NAMINGS, ids=[naming.label for naming in NAMINGS])
@pytest.mark.parametrize("match_attrs", ([], None), ids=["empty", "absent"])
def test_empty_match_attrs_means_no_relationship_matching(
    naming: _Naming,
    match_attrs: typing.Optional[typing.List[str]],
) -> None:
    """spec.md:346 -- empty or absent `match_attrs` means no relationship."""
    matcher = _matcher()
    parents = [_render(_P0, naming)]
    child = _render(_P0, naming)
    packet = _packet(naming)
    if match_attrs is None:
        packet.pop("match_attrs")
    else:
        packet["match_attrs"] = []

    index, ambiguous = _selection(matcher(parents, child, packet), parents)

    assert index is None, "spec.md:346 -- no match_attrs means no matching at all"
    assert ambiguous is False


@pytest.mark.parametrize("naming", NAMINGS, ids=[naming.label for naming in NAMINGS])
def test_no_parents_means_no_selection(naming: _Naming) -> None:
    """`statement.py@2797b5e:3781-3783`."""
    matcher = _matcher()
    index, ambiguous = _selection(matcher([], _render(_P0, naming), _packet(naming)), [])

    assert index is None
    assert ambiguous is False


@pytest.mark.parametrize("naming", NAMINGS, ids=[naming.label for naming in NAMINGS])
@pytest.mark.parametrize("row", BEHAVIOR_TABLE, ids=[row.row_id for row in BEHAVIOR_TABLE])
def test_output_names_cannot_change_selection(row: Row, naming: _Naming) -> None:
    """spec.md:343-345 and design.md:384-388 -- `parent_output_field` and
    `unmatched_child_group` name rendered arrays only; they never change
    matching, identity, or direction.
    """
    matcher = _matcher()
    parents = [_render(parent, naming) for parent in row.parents]
    child = _render(row.child, naming)

    baseline = _selection(matcher(parents, child, _packet(naming, strategy=row.strategy)), parents)
    renamed = _selection(
        matcher(
            parents,
            child,
            _packet(
                naming,
                strategy=row.strategy,
                parent_output_field="zz_renamed_output",
                unmatched_child_group="zz_renamed_unmatched",
            ),
        ),
        parents,
    )

    assert renamed == baseline == (row.expected_index, row.ambiguous), (
        f"{row.row_id} ({naming.label}) output naming must not change selection"
    )


@pytest.mark.parametrize("row", BEHAVIOR_TABLE, ids=[row.row_id for row in BEHAVIOR_TABLE])
def test_renamed_generic_parity(row: Row) -> None:
    """spec.md:373-375 -- Arcadia and renamed-generic parity proves the contract
    is general.  Group and attribute spelling cannot change the outcome.
    """
    matcher = _matcher()
    results = []
    for naming in NAMINGS:
        parents = [_render(parent, naming) for parent in row.parents]
        child = _render(row.child, naming)
        results.append(
            _selection(matcher(parents, child, _packet(naming, strategy=row.strategy)), parents)
        )

    assert results[0] == results[1] == (row.expected_index, row.ambiguous), (
        f"{row.row_id} arcadia/generic parity; cite: {row.cite}"
    )
