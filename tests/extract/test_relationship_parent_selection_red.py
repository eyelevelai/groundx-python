"""RED tests for task 3.2a7b: the one exported parent-selection primitive.

These tests are written BEFORE the implementation and are expected to FAIL.
They encode the charge-to-meter parent-selection behavior table recovered from
Internal Arcadia source history, expressed against the generic SDK contract.

Legacy source of truth (repo checkout `/private/tmp/codex-internal-merge-20260803`):

* implementation: `classes/statement.py::Statement.get_charge_meter`
  - `main` @ `2797b5e` lines 3776-3850 (current)
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
  (`ExtractedField.equal_to_value`: lowercases, int/float-normalizes, and does
  NOT strip whitespace)
* emptiness: `classes/image_evidence.py` lines 273-285 (`is_empty_source_value`)
* contract: `openspec/changes/complete-extraction-boundary-regression-coverage/`
  `tasks.md` 1355-1378 (3.2a7b), 1379-1400 (3.2a7c), `design.md` 380-411,
  `specs/extraction-boundary-regression/spec.md` 335-375

PROVENANCE LABELS
-----------------
Every row carries one provenance label, surfaced in its test id:

* ``ASSERTION`` -- a named legacy test asserts this exact outcome.
* ``DERIVED``   -- no legacy assertion covers it; the outcome follows from the
  cited implementation lines only.  Test id suffix ``__DERIVED``.
* ``MAIN_ONLY`` -- the behavior comes from Internal Arcadia `main` @ `2797b5e`,
  a revision `tasks.md:1358-1360` does not name (it scopes 3.2a7b to
  `0c359e45` plus the later cases of `d4f8ead`/`24a490c`).  Adopting current
  main needs plan-owner ratification.  Marked ``pending_authorization``.
* ``PENDING``   -- the target outcome is genuinely unresolved and is on the
  plan-owner question list.  The assertion here is NOT a ratified target.
  Marked ``pending_decision``.

Run ``pytest -m "not pending_decision and not pending_authorization"`` to see
only the ratified rows.

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
result exposing `.parent` / `.ambiguous` (attribute or mapping form) and a bare
parent-record-or-None return are accepted by `_selection` below; ambiguity
assertions require a form that can express it.
"""

import json
import pathlib
import typing

import pytest

import groundx.extract as extract

_MATCHER_NAME = "select_relationship_parent"

_MISSING = object()

ASSERTION = "assertion"
DERIVED = "derived"
MAIN_ONLY = "main_only"
PENDING = "pending"

_MARKS: typing.Mapping[str, typing.Tuple[typing.Any, ...]] = {
    ASSERTION: (),
    DERIVED: (),
    MAIN_ONLY: (pytest.mark.pending_authorization,),
    PENDING: (pytest.mark.pending_decision,),
}

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
    provenance: str
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
    provenance: str = ASSERTION,
) -> Row:
    return Row(
        row_id=row_id,
        parents=tuple(parents),
        child=child,
        expected_index=expected_index,
        stage=stage,
        ambiguous=ambiguous,
        strategy=strategy,
        provenance=provenance,
        cite=cite,
    )


_P0 = {_M: "12", _P: "Test", _S: "water"}
_P0_CONFLICTED = {_M: "12", _P: "Test", _S: "water", "P__conflicts": ["Other"]}
_STMT = "internal-arcadia classes/test_statement.py@2797b5e"
_IMPL = "internal-arcadia classes/statement.py@2797b5e"
_IMPL_24 = "internal-arcadia classes/statement.py@24a490c"

# `24a490c` (== `d4f8ead`) lacks two behaviors that `2797b5e` adds:
#   * the `populated_keys` filter to `charge_policy.match_attrs` and to
#     non-empty values (`2797b5e:3785-3792` vs `24a490c:3114-3115`, a bare
#     `if len(keys) < 1: return`); and
#   * treating an empty parent-side value as absent rather than as a mismatch
#     (`2797b5e:3799`, `:3807-3812`).
# Rows relying on either are labeled MAIN_ONLY.  Where the asserted outcome is
# nonetheless identical under `24a490c` (reached through the fallback pass
# instead of the exact pass) the citation says so.
_MAIN_ONLY_NOTE = (
    "MAIN_ONLY: relies on the 2797b5e populated_keys/empty-is-absent semantics "
    f"({_IMPL}:3785-3792, :3799, :3807-3812) which {_IMPL_24}:3114-3124 lacks; "
    "tasks.md:1358-1360 names only 0c359e45/d4f8ead/24a490c, so adopting current "
    "main needs plan-owner ratification"
)

# The accepted boundary inputs disagree on `multiple_match_strategy`:
# arcadia_legacy declares `first_stable` on its persisted relationship while
# arcadia_v1 and generic_v1 declare no strategy at all.  Under R16 that makes
# the three surfaces produce different ambiguity outcomes on multi-exact input,
# which contradicts the parity spec.md:374-375 requires.  Unresolved; on the
# plan-owner question list.  See
# `test_pending_accepted_inputs_declare_one_ambiguity_strategy` below.
_PARITY_CONTRADICTION = (
    "PENDING_DECISION: accepted inputs disagree on multiple_match_strategy "
    "(arcadia_legacy declares first_stable; arcadia_v1 and generic_v1 declare "
    "none), so under this row the three surfaces cannot satisfy the parity "
    "spec.md:374-375 requires. Unresolved -- plan-owner question, not a target."
)

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
        f"{_IMPL}:3843-3850 (unique-candidate requirement). DERIVED: no legacy "
        f"assertion covers two DISTINCT parent records here -- the two-meter input "
        f"at {_STMT}:5670-5701 collapses to one conflicted record via add_meter's "
        f"same_meter/add_conflict merge ({_IMPL}:3343-3357), which is R11/R12.",
        provenance=DERIVED,
    ),
    _row(
        "R14_exact_wins_over_ambiguous_fallback",
        [_P0, {_M: "12", _P: "Other", _S: "water"}],
        {_M: "12", _P: "Other", _S: "water"},
        1,
        "exact",
        f"{_IMPL}:3805-3819 (the exact pass precedes the fallback). DERIVED: no "
        f"legacy assertion covers two distinct parents where exactly ONE matches "
        f"exactly. {_STMT}:5703-5744 does hold two distinct parents, but there "
        f"BOTH match exactly (R15/R16); {_STMT}:5670-5701 collapses to one record.",
        provenance=DERIVED,
    ),
    # --- more than one exact candidate: declared strategy only ------------
    _row(
        "R15_multiple_exact_first_stable",
        [{_M: "M-1", _P: "Utility", _S: "water"}, {_M: "m-1", _P: "utility", _S: "WATER"}],
        {_M: "M-1", _P: "Utility", _S: "water"},
        0,
        "exact",
        f"{_STMT}:5743-5744 (asserted with first_stable declared); {_IMPL}:3818-3819; "
        f"groundx/extract/classes/field.py:85-90 (case-insensitive). "
        f"NOTE: fixture-level parity for this row is blocked -- {_PARITY_CONTRADICTION}",
        strategy="first_stable",
    ),
    _row(
        "R16_multiple_exact_without_strategy_is_ambiguous",
        [{_M: "M-1", _P: "Utility", _S: "water"}, {_M: "m-1", _P: "utility", _S: "WATER"}],
        {_M: "M-1", _P: "Utility", _S: "water"},
        None,
        "none",
        "DELIBERATE DIVERGENCE from legacy assertion "
        f"{_STMT}:5741, which returns the first candidate with NO declared strategy. "
        "openspec tasks.md:1365-1366 'Ambiguity follows only the packet's declared "
        "strategy' and tasks.md:1381-1382 'Delete the unconditional direct_matches[0] "
        f"result'. {_PARITY_CONTRADICTION}",
        ambiguous=True,
        provenance=PENDING,
    ),
    # --- reviewed available-identity matrix -------------------------------
    _row("R17_exact_full_match", [{_M: "M-1", _P: "Utility", _S: "water"}], {_M: "M-1", _P: "Utility", _S: "water"}, 0, "exact", f"{_STMT}:5754-5759"),
    _row("R18_passthrough_mismatch_unique_stable", [{_M: "M-1", _P: "Utility", _S: "water"}], {_M: "M-1", _P: "Other Utility", _S: "water"}, 0, "fallback", f"{_STMT}:5760-5773"),
    _row("R19_missing_child_side", [{_M: "M-1", _P: "Utility", _S: "water"}], {_M: "M-1", _S: "water"}, 0, "fallback", f"{_STMT}:5774-5783"),
    _row("R20_missing_parent_side", [{_M: "M-1", _S: "water"}], {_M: "M-1", _P: "Utility", _S: "water"}, 0, "fallback", f"{_STMT}:5784-5793"),
    _row("R21_missing_both_sides", [{_M: "M-1", _S: "water"}], {_M: "M-1", _S: "water"}, 0, "exact", f"{_STMT}:5794-5799"),
    # --- empty passthrough values are absent, not mismatching -------------
    # `24a490c` divergence, verified by reading `24a490c:3114-3124`:
    #   * a None-valued key reaches `equal_to_value`, which raises at
    #     `field.py:77-78`, so R22a has no defined `24a490c` outcome;
    #   * R22b/c and R23a/b/c reach the same matched outcome under `24a490c`
    #     through the fallback pass;
    #   * R24a/b/c also match under `24a490c`, but through the fallback pass
    #     rather than the exact pass -- the stage differs, the asserted index
    #     does not.
    _row(
        "R22a_none_child_side",
        [{_M: "M-1", _P: "Utility", _S: "water"}],
        {_M: "M-1", _P: None, _S: "water"},
        0,
        "fallback",
        f"{_STMT}:5801-5830; image_evidence.py:273-277. {_MAIN_ONLY_NOTE}. Under "
        f"{_IMPL_24} a None-valued key reaches equal_to_value and raises "
        "(field.py:77-78), so this row has NO defined 24a490c outcome.",
        provenance=MAIN_ONLY,
    ),
    _row(
        "R22b_blank_child_side",
        [{_M: "M-1", _P: "Utility", _S: "water"}],
        {_M: "M-1", _P: "", _S: "water"},
        0,
        "fallback",
        f"{_STMT}:5801-5830; image_evidence.py:273-277. {_MAIN_ONLY_NOTE}. Same "
        f"matched index under {_IMPL_24} via the fallback pass.",
        provenance=MAIN_ONLY,
    ),
    _row(
        "R22c_whitespace_child_side",
        [{_M: "M-1", _P: "Utility", _S: "water"}],
        {_M: "M-1", _P: "   ", _S: "water"},
        0,
        "fallback",
        f"{_STMT}:5801-5830; image_evidence.py:273-277. {_MAIN_ONLY_NOTE}. Same "
        f"matched index under {_IMPL_24} via the fallback pass.",
        provenance=MAIN_ONLY,
    ),
    _row(
        "R23a_none_parent_side",
        [{_M: "M-1", _P: None, _S: "water"}],
        {_M: "M-1", _P: "Utility", _S: "water"},
        0,
        "fallback",
        f"{_STMT}:5801-5830. {_MAIN_ONLY_NOTE}. Same matched index under "
        f"{_IMPL_24} via the fallback pass.",
        provenance=MAIN_ONLY,
    ),
    _row(
        "R23b_blank_parent_side",
        [{_M: "M-1", _P: "", _S: "water"}],
        {_M: "M-1", _P: "Utility", _S: "water"},
        0,
        "fallback",
        f"{_STMT}:5801-5830. {_MAIN_ONLY_NOTE}. Same matched index under "
        f"{_IMPL_24} via the fallback pass.",
        provenance=MAIN_ONLY,
    ),
    _row(
        "R23c_whitespace_parent_side",
        [{_M: "M-1", _P: "   ", _S: "water"}],
        {_M: "M-1", _P: "Utility", _S: "water"},
        0,
        "fallback",
        f"{_STMT}:5801-5830. {_MAIN_ONLY_NOTE}. Same matched index under "
        f"{_IMPL_24} via the fallback pass.",
        provenance=MAIN_ONLY,
    ),
    _row(
        "R24a_none_both_sides",
        [{_M: "M-1", _P: None, _S: "water"}],
        {_M: "M-1", _P: None, _S: "water"},
        0,
        "exact",
        f"{_STMT}:5801-5830. {_MAIN_ONLY_NOTE}. Under {_IMPL_24} the same index "
        "matches through the FALLBACK pass, not the exact pass.",
        provenance=MAIN_ONLY,
    ),
    _row(
        "R24b_blank_both_sides",
        [{_M: "M-1", _P: "", _S: "water"}],
        {_M: "M-1", _P: "", _S: "water"},
        0,
        "exact",
        f"{_STMT}:5801-5830. {_MAIN_ONLY_NOTE}. Under {_IMPL_24} the same index "
        "matches through the FALLBACK pass, not the exact pass.",
        provenance=MAIN_ONLY,
    ),
    _row(
        "R24c_whitespace_both_sides",
        [{_M: "M-1", _P: "   ", _S: "water"}],
        {_M: "M-1", _P: "   ", _S: "water"},
        0,
        "exact",
        f"{_STMT}:5801-5830. {_MAIN_ONLY_NOTE}. Under {_IMPL_24} the same index "
        "matches through the FALLBACK pass, not the exact pass.",
        provenance=MAIN_ONLY,
    ),
    # --- comparison normalization ----------------------------------------
    _row(
        "R25a_case_insensitive_equality",
        [{_M: "M-1", _P: "TEST", _S: "Water"}],
        {_M: "m-1", _P: "test", _S: "water"},
        0,
        "exact",
        f"{_STMT}:5709-5744 (M-1/m-1, Utility/utility, water/WATER all compare "
        "equal); groundx/extract/classes/field.py:85-90 lowercases both sides",
    ),
    _row(
        "R25b_whitespace_is_NOT_trimmed_in_legacy",
        [{_M: " 12 ", _P: "Test", _S: "water"}],
        {_M: "12", _P: "Test", _S: "water"},
        None,
        "none",
        "PENDING_DECISION -- asserts the LEGACY outcome, which is UNMATCHED. "
        "groundx/extract/classes/field.py:76-90 lowercases and int/float-normalizes "
        "but does NOT strip, so ' 12 ' != '12'; the exact pass fails on M and the "
        "fallback fails too because M is a stable attr. Internal Arcadia DOES trim "
        f"in a different primitive ({_IMPL}:3852-3856 `_identity_key_value`), but "
        "get_charge_meter never calls it. The SDK's own _normalize_match_value "
        "(src/groundx/extract/custom_outputs.py:1703-1706) DOES strip, so building "
        "the primitive on it would flip this row to matched. tasks.md:1366-1367 "
        "'Do not generalize beyond the source cases' forbids adopting trimming "
        "silently. Plan-owner question: legacy-exact or SDK-superset?",
        provenance=PENDING,
    ),
    # --- conflict handling is scoped to the ignored fields only -----------
    _row(
        "R26_conflict_on_stable_field_does_not_block",
        [{_M: "12", _P: "Test", _S: "water", "M__conflicts": ["13"]}],
        {_M: "12", _S: "water"},
        0,
        "fallback",
        f"{_IMPL}:3830-3841 -- only ignored_match_attrs are conflict-checked. "
        "DERIVED: no legacy assertion covers a conflict on a stable match field.",
        provenance=DERIVED,
    ),
    _row(
        "R27_empty_conflicts_list_does_not_block",
        [{_M: "12", _P: "Test", _S: "water", "P__conflicts": []}],
        {_M: "12", _S: "water"},
        0,
        "fallback",
        f"{_IMPL}:3839 -- truthiness of Field.conflicts. DERIVED: no legacy "
        "assertion covers an empty conflicts list.",
        provenance=DERIVED,
    ),
)

_FALLBACK_ROWS = tuple(row for row in BEHAVIOR_TABLE if row.stage == "fallback")


def _row_id(row: Row) -> str:
    if row.provenance == ASSERTION:
        return row.row_id
    return f"{row.row_id}__{row.provenance.upper()}"


def _params(rows: typing.Sequence[Row]) -> typing.List[typing.Any]:
    return [pytest.param(row, id=_row_id(row), marks=_MARKS[row.provenance]) for row in rows]


ALL_ROW_PARAMS = _params(BEHAVIOR_TABLE)
FALLBACK_ROW_PARAMS = _params(_FALLBACK_ROWS)
NAMING_PARAMS = [pytest.param(naming, id=naming.label) for naming in NAMINGS]


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
    """Normalize the primitive's result to (parent_index_or_None, ambiguous).

    Accepted result shapes:

    * ``None`` -- unmatched, not ambiguous;
    * an object or mapping carrying ``parent`` and/or ``ambiguous``; or
    * a bare parent record (a mapping carrying neither key).
    """
    if result is None:
        return None, False

    if isinstance(result, typing.Mapping):
        if "parent" not in result and "ambiguous" not in result:
            # A bare parent record.  No behavior-table record uses "parent" or
            # "ambiguous" as a field name, so this branch is unambiguous.
            return _index_of(result, parents), False
        parent = result.get("parent", _MISSING)
        ambiguous_raw = result.get("ambiguous", _MISSING)
    else:
        parent = getattr(result, "parent", _MISSING)
        ambiguous_raw = getattr(result, "ambiguous", _MISSING)

    if parent is _MISSING and ambiguous_raw is _MISSING:
        raise AssertionError(
            "task 3.2a7b contract: the selection result must expose the selected "
            f"parent as `parent` and declared ambiguity as `ambiguous`; got {result!r}"
        )
    if ambiguous_raw is _MISSING:
        raise AssertionError(
            "task 3.2a7b contract: the selection result must report declared "
            f"ambiguity as `ambiguous`; got {result!r}"
        )
    ambiguous = bool(ambiguous_raw)
    if parent is _MISSING or parent is None:
        return None, ambiguous
    return _index_of(parent, parents), ambiguous


def test_one_parent_selection_primitive_is_exported() -> None:
    assert _MATCHER_NAME in extract.__all__, (
        "task 3.2a7b contract: the parent-selection primitive must be a declared "
        f"public export of groundx.extract; __all__ lacks {_MATCHER_NAME!r}"
    )
    assert callable(_matcher())


@pytest.mark.parametrize("naming", NAMING_PARAMS)
@pytest.mark.parametrize("row", ALL_ROW_PARAMS)
def test_behavior_table(row: Row, naming: _Naming) -> None:
    matcher = _matcher()
    parents = [_render(parent, naming) for parent in row.parents]
    child = _render(row.child, naming)
    packet = _packet(naming, strategy=row.strategy)

    index, ambiguous = _selection(matcher(parents, child, packet), parents)

    assert index == row.expected_index, (
        f"{row.row_id} ({naming.label}, provenance={row.provenance}) expected parent "
        f"index {row.expected_index} via {row.stage}; cite: {row.cite}"
    )
    assert ambiguous is row.ambiguous, (
        f"{row.row_id} ({naming.label}, provenance={row.provenance}) expected "
        f"ambiguous={row.ambiguous}; cite: {row.cite}"
    )


@pytest.mark.parametrize("naming", NAMING_PARAMS)
@pytest.mark.parametrize("row", ALL_ROW_PARAMS)
def test_behavior_table_camel_case_packet_parity(row: Row, naming: _Naming) -> None:
    """Dispatched camelCase packets must select exactly what snake_case selects.

    design.md:394-396 -- Cashbot persists `parent_passthrough_attrs` /
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


@pytest.mark.parametrize("naming", NAMING_PARAMS)
@pytest.mark.parametrize("row", FALLBACK_ROW_PARAMS)
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


@pytest.mark.parametrize("naming", NAMING_PARAMS)
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


@pytest.mark.parametrize("naming", NAMING_PARAMS)
@pytest.mark.parametrize("match_attrs", ([], None), ids=["empty", "absent"])
def test_empty_match_attrs_means_no_relationship_matching(
    naming: _Naming,
    match_attrs: typing.Optional[typing.List[str]],
) -> None:
    """spec.md:345 -- empty or absent `match_attrs` means no relationship."""
    matcher = _matcher()
    parents = [_render(_P0, naming)]
    child = _render(_P0, naming)
    packet = _packet(naming)
    if match_attrs is None:
        packet.pop("match_attrs")
    else:
        packet["match_attrs"] = []

    index, ambiguous = _selection(matcher(parents, child, packet), parents)

    assert index is None, "spec.md:345 -- no match_attrs means no matching at all"
    assert ambiguous is False


@pytest.mark.parametrize("naming", NAMING_PARAMS)
def test_no_parents_means_no_selection(naming: _Naming) -> None:
    """`statement.py@2797b5e:3781-3783`."""
    matcher = _matcher()
    index, ambiguous = _selection(matcher([], _render(_P0, naming), _packet(naming)), [])

    assert index is None
    assert ambiguous is False


@pytest.mark.parametrize("naming", NAMING_PARAMS)
@pytest.mark.parametrize("row", ALL_ROW_PARAMS)
def test_output_names_cannot_change_selection(row: Row, naming: _Naming) -> None:
    """design.md:384-388 -- `parent_output_field` and `unmatched_child_group`
    name the rendered matched and unmatched arrays.  They "do not change
    matching, identity, or direction".
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


@pytest.mark.parametrize("row", ALL_ROW_PARAMS)
def test_renamed_generic_parity(row: Row) -> None:
    """spec.md:374-375 -- Arcadia and renamed-generic parity is required proof
    that the contract is general.  Group and attribute spelling cannot change
    the outcome (spec.md:369-371).
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


_BOUNDARY_INPUTS = pathlib.Path(__file__).parent / "fixtures" / "extraction-boundary" / "inputs"


def _accepted_relationship(surface: str) -> typing.Mapping[str, typing.Any]:
    payload = json.loads(
        (
            _BOUNDARY_INPUTS / surface / "internal_arcadia_download_workflow_load.handoff.json"
        ).read_text()
    )
    relationships = payload["workflow_extract"]["_groundx_persisted_extract"]["workflow"][
        "output_relationships"
    ]
    assert len(relationships) == 1, surface
    return relationships[0]


@pytest.mark.pending_decision
def test_pending_accepted_inputs_declare_one_ambiguity_strategy() -> None:
    """PENDING_DECISION -- not a ratified target.

    spec.md:374-375 requires Arcadia and renamed-generic parity as proof of the
    general contract.  Under behavior-table row R16, a workflow with no declared
    `multiple_match_strategy` treats multiple exact candidates as ambiguous,
    while `first_stable` selects the first.  The accepted boundary inputs do not
    agree on that declaration, so the three surfaces cannot produce identical
    ambiguity outcomes on multi-exact input.  This is an input problem for
    3.2a7b/3.2a7d, not a test bug, and it is on the plan-owner question list.
    """
    declared = {
        surface: _accepted_relationship(surface).get("multiple_match_strategy")
        for surface in ("arcadia_legacy", "arcadia_v1", "generic_v1")
    }

    assert len(set(declared.values())) == 1, (
        "accepted inputs disagree on multiple_match_strategy, so the parity "
        f"spec.md:374-375 requires cannot hold under R16: {declared}"
    )
