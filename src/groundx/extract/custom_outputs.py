from __future__ import annotations

import copy
import dataclasses
import json
import numbers
import typing

from .comparison import match_key, values_match
from .utility import clean_json


@dataclasses.dataclass(frozen=True)
class CustomOutputDiagnostic:
    code: str
    message: str
    severity: str = "error"
    workflow_group: typing.Optional[str] = None
    workflow_field: typing.Optional[str] = None
    final_path: typing.Optional[str] = None
    relationship: typing.Optional[str] = None
    child_record_index: typing.Optional[int] = None


@dataclasses.dataclass(frozen=True)
class CustomOutputSourceProvenance:
    output_source: str
    workflow_group: str
    workflow_field: str
    final_path: str
    record_index: typing.Optional[int]
    page_numbers: typing.Tuple[int, ...] = ()


@dataclasses.dataclass(frozen=True)
class CustomOutputFinalRecordProvenance:
    final_path: str
    page_numbers: typing.Tuple[int, ...] = ()


@dataclasses.dataclass(frozen=True)
class CustomOutputScalarCandidate:
    value: typing.Any
    page_numbers: typing.Tuple[int, ...] = ()


@dataclasses.dataclass(frozen=True)
class CustomOutputScalarCandidateSet:
    """Observed values for one singular route in traversal order.

    ``selected`` is the first observed candidate and remains provisional when
    ``alternatives`` is non-empty. Later unique observations appear in
    ``alternatives`` without SDK value selection.
    """

    output_source: str
    workflow_group: str
    workflow_field: str
    final_path: str
    selected: CustomOutputScalarCandidate
    alternatives: typing.Tuple[CustomOutputScalarCandidate, ...] = ()


@dataclasses.dataclass(frozen=True)
class CustomOutputReassemblyResult:
    """Custom-output route reassembly and diagnostic evidence.

    ``final_output`` contains the first observed scalar candidate. A scalar
    value remains provisional when its candidate set has alternatives.
    """

    final_output: typing.Dict[str, typing.Any]
    relationship_output: typing.Optional[typing.Dict[str, typing.Any]]
    diagnostics: typing.List[CustomOutputDiagnostic]
    workflow_output: typing.Dict[str, typing.Any] = dataclasses.field(default_factory=dict)
    source_provenance: typing.List[CustomOutputSourceProvenance] = dataclasses.field(default_factory=list)
    final_record_provenance: typing.List[CustomOutputFinalRecordProvenance] = dataclasses.field(default_factory=list)
    scalar_candidate_sets: typing.List[CustomOutputScalarCandidateSet] = dataclasses.field(default_factory=list)


@dataclasses.dataclass(frozen=True)
class RelationshipParentSelection:
    """Result of :func:`select_relationship_parent` (task 3.2a7b).

    ``parent`` is the selected parent record, or ``None`` when no parent was
    selected. ``ambiguous`` remains for API compatibility and is always
    ``False``. Multiple matches select the first parent in stable input order.
    """

    parent: typing.Optional[typing.Mapping[str, typing.Any]] = None
    ambiguous: bool = False


@dataclasses.dataclass(frozen=True)
class _RouteValue:
    value: typing.Any
    record_index: typing.Optional[int]
    repeated: bool
    conflicts: typing.Optional[typing.List[typing.Any]] = None


@dataclasses.dataclass(frozen=True)
class _RouteContainer:
    identity: typing.Tuple[typing.Any, ...]
    value: typing.Any
    page_numbers: typing.Tuple[int, ...] = ()


class _LineagedRecord(dict[str, typing.Any]):
    page_numbers: typing.Tuple[int, ...]

    def __init__(self) -> None:
        super().__init__()
        self.page_numbers = ()


@dataclasses.dataclass(frozen=True)
class _ScalarCandidate:
    value: typing.Any
    page_numbers: typing.Tuple[int, ...]


@dataclasses.dataclass(frozen=True)
class _ScalarCandidateState:
    selected: _ScalarCandidate
    alternatives: typing.Tuple[_ScalarCandidate, ...]
    route: typing.Mapping[str, typing.Any]


_REPEATED_STEP_KINDS = {"keys", "summary"}
_EXTRACTED_FIELD_VALUE_KEYS = {"value", "_raw_text", "confidence", "conflicts", "qa"}
_CONFLICTS_SIBLING_SUFFIX = "__conflicts"
_RELATIONSHIP_PACKET_CAMEL_KEYS = {
    "match_attrs": "matchAttrs",
    # Historical packet aliases are accepted but ignored.
    "parent_passthrough_attrs": "parentPassthroughAttrs",
    "multiple_match_strategy": "multipleMatchStrategy",
}
_GET_ALIASES = {
    "chunkId": ("chunk_id",),
    "customChunkOutputs": ("custom_chunk_outputs",),
    "customDocumentOutputs": ("custom_document_outputs",),
    "customSectionOutputs": ("custom_section_outputs",),
    "documentPages": ("document_pages",),
    "pageNumbers": ("page_numbers",),
    "sectionId": ("section_id",),
}


def reassemble_custom_outputs_from_xray(
    xray: typing.Any,
    *,
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]] = None,
) -> CustomOutputReassemblyResult:
    workflow = _workflow_metadata(workflow_extract)
    routes = workflow.get("output_routes") if workflow else None
    if not isinstance(routes, list):
        return CustomOutputReassemblyResult(
            final_output={},
            relationship_output=None,
            diagnostics=[],
        )

    step_kinds = _custom_step_kinds(workflow)
    final_output: typing.Dict[str, typing.Any] = {}
    workflow_output: typing.Dict[str, typing.Any] = {}
    source_provenance: typing.List[CustomOutputSourceProvenance] = []
    route_satisfied: typing.Dict[int, bool] = {}
    repeated_records: typing.Dict[
        typing.Tuple[typing.Tuple[str, ...], typing.Tuple[typing.Any, ...]],
        typing.Dict[str, typing.Any],
    ] = {}
    scalar_candidates: typing.Dict[str, _ScalarCandidateState] = {}
    workflow_repeated_records: typing.Dict[
        typing.Tuple[str, typing.Tuple[typing.Any, ...]],
        typing.Dict[str, typing.Any],
    ] = {}
    repeated_group_paths: typing.Dict[
        str,
        typing.Set[typing.Tuple[str, ...]],
    ] = {}
    diagnostics: typing.List[CustomOutputDiagnostic] = []

    for route_index, route in enumerate(routes):
        route_satisfied[route_index] = False
        if not isinstance(route, dict):
            continue
        route_map = typing.cast(typing.Mapping[str, typing.Any], route)
        final_path = route_map.get("final_path")
        if not isinstance(final_path, str):
            continue
        route_repeats = _repeated_route(route_map, step_kinds)

        for route_container in _route_containers(
            xray,
            route_map,
            repeated=route_repeats,
        ):
            for route_value in _custom_route_values(
                route_container.value,
                route_map,
                step_kinds=step_kinds,
            ):
                pointer = final_path
                record_key = (
                    *route_container.identity,
                    route_map.get("step_name"),
                    route_value.record_index,
                )
                if route_value.repeated and _is_empty_output(route_value.value):
                    if route_value.conflicts:
                        _set_pointer(
                            final_output,
                            f"{pointer}{_CONFLICTS_SIBLING_SUFFIX}",
                            copy.deepcopy(route_value.conflicts),
                            repeated_records=repeated_records,
                            record_key=record_key,
                            route=route_map,
                            page_numbers=route_container.page_numbers,
                            scalar_candidates=scalar_candidates,
                            diagnostics=diagnostics,
                            repeated=route_repeats,
                        )
                    continue
                if route_value.repeated or _unwrap_match_value(route_value.value) is not None:
                    route_satisfied[route_index] = True
                if route_repeats:
                    _record_repeated_group_path(
                        repeated_group_paths,
                        pointer,
                    )
                _set_workflow_value(
                    workflow_output,
                    route_map,
                    route_value,
                    repeated_records=workflow_repeated_records,
                    record_key=record_key,
                )
                source_provenance.extend(
                    _source_provenance(
                        route_map,
                        route_value,
                        page_numbers=route_container.page_numbers,
                    )
                )
                _set_pointer(
                    final_output,
                    pointer,
                    copy.deepcopy(route_value.value),
                    repeated_records=repeated_records,
                    record_key=record_key,
                    route=route_map,
                    page_numbers=route_container.page_numbers,
                    scalar_candidates=scalar_candidates,
                    diagnostics=diagnostics,
                    repeated=route_repeats,
                )
                if route_value.repeated and route_value.conflicts is not None:
                    # Preserve the generic `<field>__conflicts` record sibling
                    # as reassembly evidence next to its field.
                    _set_pointer(
                        final_output,
                        f"{pointer}{_CONFLICTS_SIBLING_SUFFIX}",
                        copy.deepcopy(route_value.conflicts),
                        repeated_records=repeated_records,
                        record_key=record_key,
                        route=route_map,
                        page_numbers=route_container.page_numbers,
                        scalar_candidates=scalar_candidates,
                        diagnostics=diagnostics,
                        repeated=route_repeats,
                    )

    _dedupe_repeated_group_outputs(
        final_output,
        repeated_group_paths,
        workflow_extract,
    )
    relationships = workflow.get("output_relationships") if workflow else None
    relationship_output = None
    diagnostics.extend(
        _missing_required_route_diagnostics(
            typing.cast(typing.Sequence[typing.Any], routes),
            route_satisfied,
            workflow_extract,
        )
    )
    if isinstance(relationships, list) and relationships:
        relationship_output, diagnostics = _apply_relationships(
            final_output,
            typing.cast(typing.Sequence[typing.Any], relationships),
            diagnostics=diagnostics,
        )
        final_output = copy.deepcopy(relationship_output)
    else:
        diagnostics.extend(
            _missing_relationship_metadata_diagnostics(
                final_output,
                workflow_extract,
            )
        )

    final_record_provenance = _final_record_provenance(final_output)
    plain_final_output = typing.cast(
        typing.Dict[str, typing.Any],
        _plain_output(final_output),
    )
    plain_relationship_output = (
        typing.cast(
            typing.Dict[str, typing.Any],
            _plain_output(relationship_output),
        )
        if relationship_output is not None
        else None
    )

    return CustomOutputReassemblyResult(
        final_output=plain_final_output,
        relationship_output=plain_relationship_output,
        diagnostics=diagnostics,
        workflow_output=workflow_output,
        source_provenance=source_provenance,
        final_record_provenance=final_record_provenance,
        scalar_candidate_sets=_public_scalar_candidate_sets(scalar_candidates),
    )


def reassemble_custom_outputs(
    xray: typing.Any,
    *,
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]] = None,
) -> CustomOutputReassemblyResult:
    return reassemble_custom_outputs_from_xray(
        xray,
        workflow_extract=workflow_extract,
    )


def select_relationship_parent(
    parents: typing.Sequence[typing.Mapping[str, typing.Any]],
    child: typing.Mapping[str, typing.Any],
    relationship: typing.Mapping[str, typing.Any],
) -> RelationshipParentSelection:
    """Select the parent record a child record belongs to.

    This is the one exported relationship parent-selection primitive.  It ports
    the legacy charge-to-meter matcher
    (``internal-arcadia classes/statement.py::Statement.get_charge_meter`` on
    ``origin/main``, with the populated-keys filter and empty-value-is-absent
    semantics adopted by owner RULING 7a, 2026-08-05; the ``2797b5e`` commit an
    earlier revision cited as "main" is a plan-branch checkpoint, not main)
    onto the generic relationship packet:

    * ``parents`` is an ordered sequence of parent records, ``child`` is one
      child record, and ``relationship`` contains ``match_attrs`` or
      ``matchAttrs``.
    * The child identity is the packet's ``match_attrs`` filtered to the
      child's populated (non-empty) values; an empty value counts as absent.
    * A parent matches when it populates exactly the same match attrs the child
      populates and every populated value compares equal. The first matching
      parent in stable input order wins.
    * Other relationship metadata does not affect parent selection.
    * String comparison ignores capitalization and whitespace and maps the
      approved OCR-confusable classes. Ints and floats remain number-normalized.
    """
    no_selection = RelationshipParentSelection(parent=None, ambiguous=False)
    if not isinstance(relationship, typing.Mapping):
        return no_selection
    if not isinstance(child, typing.Mapping):
        return no_selection

    match_attrs = _relationship_attr_list(_relationship_packet_value(relationship, "match_attrs"))
    if not match_attrs:
        return no_selection

    parent_list = [parent for parent in (parents or []) if isinstance(parent, typing.Mapping)]
    if not parent_list:
        return no_selection

    populated_keys = {attr: child.get(attr) for attr in match_attrs if not _relationship_value_absent(child.get(attr))}
    if not populated_keys:
        return no_selection

    def matches_attrs(parent: typing.Mapping[str, typing.Any]) -> bool:
        for attr, child_value in populated_keys.items():
            parent_value = parent.get(attr)
            if _relationship_value_absent(parent_value):
                return False
            parent_unwrapped = _unwrap_match_value(parent_value)
            child_unwrapped = _unwrap_match_value(child_value)
            if isinstance(parent_unwrapped, str) and isinstance(child_unwrapped, str):
                if not values_match(parent_unwrapped, child_unwrapped):
                    return False
                continue
            if _relationship_comparison_value(parent_value) != _relationship_comparison_value(child_value):
                return False
        return True

    for parent in parent_list:
        parent_key_count = sum(1 for attr in match_attrs if not _relationship_value_absent(parent.get(attr)))
        if parent_key_count == len(populated_keys) and matches_attrs(parent):
            return RelationshipParentSelection(parent=parent, ambiguous=False)
    return no_selection


def custom_output_payload_identity(value: typing.Any) -> str:
    return _record_key(_plain(value))


def custom_output_section_identity(
    chunk: typing.Any,
    output_map_name: str = "customSectionOutputs",
) -> str:
    output_payload = _get(chunk, output_map_name)
    section_id = _section_identifier(chunk)
    if section_id is not None:
        return _record_key((output_map_name, "section", section_id))

    payload_identity = custom_output_payload_identity(output_payload)
    page_numbers = _page_numbers(chunk)
    if page_numbers:
        return _record_key((output_map_name, "payload_pages", payload_identity, page_numbers))
    return _record_key((output_map_name, "payload", payload_identity))


def custom_output_route_values(
    custom_outputs: typing.Mapping[str, typing.Any],
    route: typing.Mapping[str, typing.Any],
    *,
    step_kinds: typing.Optional[typing.Mapping[str, str]] = None,
) -> typing.List[_RouteValue]:
    output_map_name = route.get("output_map")
    if not isinstance(output_map_name, str):
        return []
    container = {output_map_name: custom_outputs}
    return _custom_route_values(
        container,
        route,
        step_kinds=step_kinds or {},
    )


def _workflow_metadata(
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]],
) -> typing.Dict[str, typing.Any]:
    if not isinstance(workflow_extract, typing.Mapping):
        return {}
    workflow = workflow_extract.get("workflow")
    if isinstance(workflow, typing.Mapping):
        return dict(typing.cast(typing.Mapping[str, typing.Any], workflow))
    return {}


def _custom_step_kinds(workflow: typing.Mapping[str, typing.Any]) -> typing.Dict[str, str]:
    step_kinds: typing.Dict[str, str] = {}
    steps = workflow.get("custom_steps")
    if not isinstance(steps, list):
        return step_kinds
    for step in steps:
        if not isinstance(step, typing.Mapping):
            continue
        name = step.get("name")
        kind = step.get("kind")
        if isinstance(name, str) and isinstance(kind, str):
            step_kinds[name] = kind
    return step_kinds


def _repeated_route(
    route: typing.Mapping[str, typing.Any],
    step_kinds: typing.Mapping[str, str],
) -> bool:
    step_name = route.get("step_name")
    final_path = route.get("final_path")
    return (isinstance(step_name, str) and step_kinds.get(step_name) in _REPEATED_STEP_KINDS) or (
        isinstance(final_path, str) and "*" in _pointer_parts(final_path)
    )


def _route_containers(
    xray: typing.Any,
    route: typing.Mapping[str, typing.Any],
    *,
    repeated: bool,
) -> typing.List[_RouteContainer]:
    level = route.get("level")
    output_map_name = route.get("output_map")
    if level == "document":
        if not isinstance(output_map_name, str):
            return [_RouteContainer(identity=("document",), value=xray)]
        document_containers: typing.List[_RouteContainer] = []
        if not repeated:
            root_output_payload = _get(xray, output_map_name)
            if isinstance(root_output_payload, typing.Mapping):
                document_containers.append(
                    _RouteContainer(
                        identity=("document", output_map_name, "root"),
                        value=xray,
                    )
                )
            for chunk in _iter_chunks(xray):
                output_payload = _get(chunk, output_map_name)
                if not isinstance(output_payload, typing.Mapping):
                    continue
                document_containers.append(
                    _RouteContainer(
                        identity=("document", output_map_name, _chunk_identity(chunk)),
                        value=chunk,
                        page_numbers=_page_numbers(chunk),
                    )
                )
            return document_containers
        document_seen: typing.Set[str] = set()
        for container in [xray, *_iter_chunks(xray)]:
            output_payload = _get(container, output_map_name)
            if not isinstance(output_payload, typing.Mapping):
                continue
            identity = custom_output_payload_identity(output_payload)
            if identity in document_seen:
                continue
            document_seen.add(identity)
            document_containers.append(
                _RouteContainer(
                    identity=("document", output_map_name, identity),
                    value=container,
                )
            )
        return document_containers
    if level == "chunk":
        return [
            _RouteContainer(
                identity=("chunk", _chunk_identity(chunk)),
                value=chunk,
                page_numbers=_page_numbers(chunk),
            )
            for chunk in _iter_chunks(xray)
        ]
    if level == "section" and isinstance(output_map_name, str):
        if not repeated:
            return [
                _RouteContainer(
                    identity=("section", output_map_name, _chunk_identity(chunk)),
                    value=chunk,
                    page_numbers=_page_numbers(chunk),
                )
                for chunk in _iter_chunks(xray)
            ]
        section_containers: typing.List[_RouteContainer] = []
        section_seen: typing.Set[str] = set()
        for chunk in _iter_chunks(xray):
            identity = custom_output_section_identity(chunk, output_map_name)
            if identity in section_seen:
                continue
            section_seen.add(identity)
            section_containers.append(
                _RouteContainer(
                    identity=("section", output_map_name, identity),
                    value=chunk,
                    page_numbers=_page_numbers(chunk),
                )
            )
        return section_containers
    return []


def _custom_route_values(
    container: typing.Any,
    route: typing.Mapping[str, typing.Any],
    *,
    step_kinds: typing.Mapping[str, str],
) -> typing.List[_RouteValue]:
    output_map_name = route.get("output_map")
    step_name = route.get("step_name")
    output_key = route.get("output_key")
    if not isinstance(output_map_name, str):
        return []
    if not isinstance(step_name, str):
        return []
    if not isinstance(output_key, str):
        return []

    output_map = _get(container, output_map_name)
    if not isinstance(output_map, typing.Mapping):
        return []

    if step_name not in output_map:
        return []
    step_value = output_map[step_name]
    route_repeats = _repeated_route(route, step_kinds)

    if isinstance(step_value, typing.Mapping):
        records = step_value.get("_records")
        if isinstance(records, list):
            record_values: typing.List[_RouteValue] = []
            for index, record in enumerate(records):
                if not isinstance(record, typing.Mapping):
                    continue
                conflicts = _record_conflicts_sibling(record, output_key)
                if output_key not in record and not conflicts:
                    continue
                record_values.append(
                    _RouteValue(
                        value=record.get(output_key),
                        record_index=index,
                        repeated=True,
                        conflicts=conflicts,
                    )
                )
            if record_values:
                return record_values

        if output_key not in step_value:
            return []
        value = step_value[output_key]
        if isinstance(value, list) and route_repeats:
            return [_RouteValue(value=item, record_index=index, repeated=True) for index, item in enumerate(value)]
        return [
            _RouteValue(
                value=value,
                record_index=0 if route_repeats else None,
                repeated=route_repeats and not isinstance(records, list),
            )
        ]

    if isinstance(step_value, list):
        if not route_repeats:
            return [
                _RouteValue(
                    value=step_value,
                    record_index=None,
                    repeated=False,
                )
            ]
        values: typing.List[_RouteValue] = []
        for index, record in enumerate(step_value):
            if isinstance(record, typing.Mapping):
                conflicts = _record_conflicts_sibling(record, output_key)
                if output_key not in record and not conflicts:
                    continue
                values.append(
                    _RouteValue(
                        value=record.get(output_key),
                        record_index=index,
                        repeated=True,
                        conflicts=conflicts,
                    )
                )
            else:
                values.append(_RouteValue(value=record, record_index=index, repeated=True))
        return values

    return [
        _RouteValue(
            value=step_value,
            record_index=0 if route_repeats else None,
            repeated=route_repeats,
        )
    ]


def _record_conflicts_sibling(
    record: typing.Mapping[str, typing.Any],
    output_key: str,
) -> typing.Optional[typing.List[typing.Any]]:
    """Read a source record's generic ``<field>__conflicts`` sibling."""
    sibling = record.get(f"{output_key}{_CONFLICTS_SIBLING_SUFFIX}")
    if isinstance(sibling, list):
        return typing.cast(typing.List[typing.Any], sibling)
    return None


def _iter_chunks(xray: typing.Any) -> typing.Iterator[typing.Any]:
    seen: typing.Set[str] = set()
    for chunk in _list_value(_get(xray, "chunks")):
        identity = _chunk_identity(chunk)
        seen.add(identity)
        yield chunk

    for page in _list_value(_get(xray, "documentPages")):
        for chunk in _list_value(_get(page, "chunks")):
            identity = _chunk_identity(chunk)
            if identity in seen:
                continue
            seen.add(identity)
            yield chunk


def _chunk_identity(chunk: typing.Any) -> str:
    for key in ("chunkId", "chunk_id", "id"):
        value = _get(chunk, key)
        if value not in (None, ""):
            return f"{key}:{value}"
    return _record_key(_plain(chunk))


def _section_identifier(chunk: typing.Any) -> typing.Optional[str]:
    for key in ("sectionId", "sectionID", "section_id", "section"):
        value = _get(chunk, key)
        if value not in (None, ""):
            return str(value)
    return None


def _page_numbers(value: typing.Any) -> typing.Tuple[int, ...]:
    raw_page_numbers = _get(value, "pageNumbers")
    if not isinstance(raw_page_numbers, list):
        raw_page_numbers = _get(value, "page_numbers")
    if not isinstance(raw_page_numbers, list):
        return ()

    seen: typing.Set[int] = set()
    page_numbers: typing.List[int] = []
    for page_number in raw_page_numbers:
        if not isinstance(page_number, int):
            continue
        if page_number in seen:
            continue
        seen.add(page_number)
        page_numbers.append(page_number)
    return tuple(page_numbers)


def _get(value: typing.Any, key: str) -> typing.Any:
    raw_value = None
    sentinel = object()
    for candidate in (key, *_GET_ALIASES.get(key, ())):
        if isinstance(value, typing.Mapping):
            candidate_value = value.get(candidate, sentinel)
        else:
            candidate_value = getattr(value, candidate, sentinel)
        if candidate_value is not sentinel:
            raw_value = candidate_value
            break
    if isinstance(raw_value, str):
        try:
            parsed_value = json.loads(clean_json(raw_value))
        except json.JSONDecodeError:
            return raw_value
        if isinstance(parsed_value, typing.Mapping):
            return parsed_value
    return raw_value


def _list_value(value: typing.Any) -> typing.List[typing.Any]:
    return value if isinstance(value, list) else []


def _plain(value: typing.Any) -> typing.Any:
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(exclude_none=True)
    if isinstance(value, typing.Mapping):
        return dict(typing.cast(typing.Mapping[str, typing.Any], value))
    return value


def _is_empty_output(value: typing.Any) -> bool:
    if value is None:
        return True
    if value == "":
        return True
    if value == []:
        return True
    return False


def _scalar_candidate(
    value: typing.Any,
    page_numbers: typing.Tuple[int, ...],
) -> _ScalarCandidate:
    retained_value = value
    if isinstance(value, str):
        retained_value = value.strip()
    elif isinstance(value, typing.Mapping) and _unwrap_match_value(value) is not value:
        retained_value = copy.deepcopy(dict(value))
        inner_value = retained_value.get("value")
        if isinstance(inner_value, str):
            retained_value["value"] = inner_value.strip()
    return _ScalarCandidate(
        value=retained_value,
        page_numbers=page_numbers,
    )


def _scalar_candidate_identity(value: typing.Any) -> typing.Any:
    """Return transport-only identity for one scalar candidate value."""
    unwrapped = _unwrap_match_value(value)
    if isinstance(unwrapped, str):
        return ("string", unwrapped.strip().casefold())

    def exact_json_identity(item: typing.Any) -> typing.Any:
        if item is None:
            return ("null",)
        if type(item) is bool:
            return ("boolean", item)
        if type(item) is int:
            return ("integer", item)
        if type(item) is float:
            return ("float", item)
        if isinstance(item, str):
            return ("string", item)
        if isinstance(item, list):
            return ("list", tuple(exact_json_identity(value) for value in item))
        if isinstance(item, typing.Mapping):
            return (
                "object",
                tuple(
                    sorted(
                        (
                            (type(key).__name__, repr(key)),
                            exact_json_identity(nested_value),
                        )
                        for key, nested_value in item.items()
                    )
                ),
            )
        return (type(item).__module__, type(item).__qualname__, repr(item))

    return exact_json_identity(unwrapped)


def _string_value(value: typing.Any) -> typing.Optional[str]:
    return value if isinstance(value, str) else None


def _set_pointer(
    result: typing.Dict[str, typing.Any],
    pointer: str,
    value: typing.Any,
    *,
    repeated_records: typing.Dict[
        typing.Tuple[typing.Tuple[str, ...], typing.Tuple[typing.Any, ...]],
        typing.Dict[str, typing.Any],
    ],
    record_key: typing.Tuple[typing.Any, ...],
    route: typing.Mapping[str, typing.Any],
    page_numbers: typing.Tuple[int, ...],
    scalar_candidates: typing.Dict[str, _ScalarCandidateState],
    diagnostics: typing.List[CustomOutputDiagnostic],
    repeated: bool,
) -> None:
    parts = _pointer_parts(pointer)
    if not parts:
        return

    if "*" in parts:
        star_index = parts.index("*")
        list_path = parts[:star_index]
        if not list_path:
            return
        current = result
        for part in list_path[:-1]:
            next_value = current.setdefault(part, {})
            if not isinstance(next_value, dict):
                return
            current = next_value

        list_name = list_path[-1]
        records = current.setdefault(list_name, [])
        if not isinstance(records, list):
            return
        item_key = (tuple(list_path), record_key)
        record = repeated_records.get(item_key)
        if record is None:
            record = _LineagedRecord()
            repeated_records[item_key] = record
            records.append(record)
        _add_record_pages(record, page_numbers)

        field_path = parts[star_index + 1 :]
        if field_path:
            _set_nested_value(record, field_path, value)
        return

    if repeated:
        records = result.setdefault(parts[0], [])
        if not isinstance(records, list):
            return
        item_key = ((parts[0],), record_key)
        record = repeated_records.get(item_key)
        if record is None:
            record = _LineagedRecord()
            repeated_records[item_key] = record
            records.append(record)
        _add_record_pages(record, page_numbers)
        if len(parts) > 1:
            _set_nested_value(record, parts[1:], value)
        return

    current = result
    for part in parts[:-1]:
        next_value = current.setdefault(part, {})
        if not isinstance(next_value, dict):
            return
        current = next_value
    candidate = _scalar_candidate(value, page_numbers)
    state = scalar_candidates.get(pointer)
    if state is not None:
        existing = state.selected
        candidate_identity = _scalar_candidate_identity(candidate.value)
        if candidate_identity == _scalar_candidate_identity(existing.value):
            scalar_candidates[pointer] = dataclasses.replace(
                state,
                selected=dataclasses.replace(
                    existing,
                    page_numbers=_merge_page_numbers(existing.page_numbers, candidate.page_numbers),
                ),
            )
            return
        for index, alternative in enumerate(state.alternatives):
            if candidate_identity != _scalar_candidate_identity(alternative.value):
                continue
            alternatives = list(state.alternatives)
            alternatives[index] = dataclasses.replace(
                alternative,
                page_numbers=_merge_page_numbers(alternative.page_numbers, candidate.page_numbers),
            )
            scalar_candidates[pointer] = dataclasses.replace(
                state,
                alternatives=tuple(alternatives),
            )
            return
        diagnostics.append(
            CustomOutputDiagnostic(
                code="conflicting_output_candidates",
                message=f"multiple candidates for [{pointer}]",
                severity="warning",
                workflow_group=_string_value(route.get("workflow_group")),
                workflow_field=_string_value(route.get("workflow_field")),
                final_path=pointer,
            )
        )
        scalar_candidates[pointer] = dataclasses.replace(
            state,
            alternatives=(*state.alternatives, candidate),
        )
        return
    current[parts[-1]] = copy.deepcopy(candidate.value)
    scalar_candidates[pointer] = _ScalarCandidateState(
        selected=candidate,
        alternatives=(),
        route=dict(route),
    )


def _merge_page_numbers(
    first: typing.Sequence[int],
    second: typing.Sequence[int],
) -> typing.Tuple[int, ...]:
    return tuple(dict.fromkeys((*first, *second)))


def _add_record_pages(
    record: typing.MutableMapping[str, typing.Any],
    page_numbers: typing.Sequence[int],
) -> None:
    if isinstance(record, _LineagedRecord):
        record.page_numbers = _merge_page_numbers(
            record.page_numbers,
            page_numbers,
        )


def _final_record_provenance(
    output: typing.Mapping[str, typing.Any],
) -> typing.List[CustomOutputFinalRecordProvenance]:
    provenance: typing.List[CustomOutputFinalRecordProvenance] = []

    def visit(value: typing.Any, parts: typing.Tuple[str, ...]) -> None:
        if isinstance(value, list):
            for index, item in enumerate(value):
                item_parts = (*parts, str(index))
                if isinstance(item, _LineagedRecord):
                    provenance.append(
                        CustomOutputFinalRecordProvenance(
                            final_path=_encode_pointer(item_parts),
                            page_numbers=item.page_numbers,
                        )
                    )
                visit(item, item_parts)
            return
        if isinstance(value, typing.Mapping):
            for key, item in value.items():
                visit(item, (*parts, str(key)))

    visit(output, ())
    return provenance


def _plain_output(value: typing.Any) -> typing.Any:
    if isinstance(value, typing.Mapping):
        return {key: _plain_output(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_output(item) for item in value]
    return copy.deepcopy(value)


def _public_scalar_candidate_sets(
    scalar_candidates: typing.Mapping[str, _ScalarCandidateState],
) -> typing.List[CustomOutputScalarCandidateSet]:
    candidate_sets: typing.List[CustomOutputScalarCandidateSet] = []
    for final_path, state in scalar_candidates.items():
        output_source = state.route.get("output_map")
        workflow_group = state.route.get("workflow_group")
        workflow_field = state.route.get("workflow_field")
        if not isinstance(output_source, str):
            continue
        if not isinstance(workflow_group, str):
            continue
        if not isinstance(workflow_field, str):
            continue
        candidate_sets.append(
            CustomOutputScalarCandidateSet(
                output_source=output_source,
                workflow_group=workflow_group,
                workflow_field=workflow_field,
                final_path=final_path,
                selected=_public_scalar_candidate(state.selected),
                alternatives=tuple(_public_scalar_candidate(candidate) for candidate in state.alternatives),
            )
        )
    return candidate_sets


def _public_scalar_candidate(candidate: _ScalarCandidate) -> CustomOutputScalarCandidate:
    return CustomOutputScalarCandidate(
        value=copy.deepcopy(candidate.value),
        page_numbers=candidate.page_numbers,
    )


def _set_workflow_value(
    workflow_output: typing.Dict[str, typing.Any],
    route: typing.Mapping[str, typing.Any],
    route_value: _RouteValue,
    *,
    repeated_records: typing.Dict[
        typing.Tuple[str, typing.Tuple[typing.Any, ...]],
        typing.Dict[str, typing.Any],
    ],
    record_key: typing.Tuple[typing.Any, ...],
) -> None:
    workflow_group = route.get("workflow_group")
    workflow_field = route.get("workflow_field")
    if not isinstance(workflow_group, str):
        return
    if not isinstance(workflow_field, str):
        return

    if route_value.repeated:
        group_records = workflow_output.setdefault(workflow_group, [])
        if not isinstance(group_records, list):
            return
        item_key = (workflow_group, record_key)
        record = repeated_records.get(item_key)
        if record is None:
            record = {}
            repeated_records[item_key] = record
            group_records.append(record)
        record[workflow_field] = copy.deepcopy(route_value.value)
        return

    group_output = workflow_output.setdefault(workflow_group, {})
    if not isinstance(group_output, dict):
        return
    group_output[workflow_field] = copy.deepcopy(route_value.value)


def _source_provenance(
    route: typing.Mapping[str, typing.Any],
    route_value: _RouteValue,
    *,
    page_numbers: typing.Tuple[int, ...],
) -> typing.List[CustomOutputSourceProvenance]:
    output_source = route.get("output_map")
    workflow_group = route.get("workflow_group")
    workflow_field = route.get("workflow_field")
    final_path = route.get("final_path")
    if not isinstance(output_source, str):
        return []
    if not isinstance(workflow_group, str):
        return []
    if not isinstance(workflow_field, str):
        return []
    if not isinstance(final_path, str):
        return []

    return [
        CustomOutputSourceProvenance(
            output_source=output_source,
            workflow_group=workflow_group,
            workflow_field=workflow_field,
            final_path=final_path,
            record_index=route_value.record_index if route_value.repeated else None,
            page_numbers=page_numbers,
        )
    ]


def _set_nested_value(
    record: typing.Dict[str, typing.Any],
    parts: typing.Tuple[str, ...],
    value: typing.Any,
) -> None:
    current = record
    for part in parts[:-1]:
        next_value = current.setdefault(part, {})
        if not isinstance(next_value, dict):
            return
        current = next_value
    current[parts[-1]] = value


def _missing_required_route_diagnostics(
    routes: typing.Sequence[typing.Any],
    route_satisfied: typing.Mapping[int, bool],
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]],
) -> typing.List[CustomOutputDiagnostic]:
    if not isinstance(workflow_extract, typing.Mapping):
        return []

    hit_workflow_groups = {
        str(route.get("workflow_group"))
        for index, route in enumerate(routes)
        if route_satisfied.get(index) and isinstance(route, typing.Mapping)
    }
    diagnostics: typing.List[CustomOutputDiagnostic] = []
    for index, route in enumerate(routes):
        if route_satisfied.get(index):
            continue
        if not isinstance(route, typing.Mapping):
            continue
        route_map = typing.cast(typing.Mapping[str, typing.Any], route)
        if not _route_is_required(route_map, workflow_extract):
            continue

        workflow_group = route_map.get("workflow_group")
        workflow_field = route_map.get("workflow_field")
        final_path = route_map.get("final_path")
        code = (
            "missing_workflow_group"
            if isinstance(workflow_group, str) and workflow_group not in hit_workflow_groups
            else "missing_workflow_field"
        )
        diagnostics.append(
            CustomOutputDiagnostic(
                code=code,
                message=(f"required workflow output [{workflow_group}.{workflow_field}] for [{final_path}] is missing"),
                workflow_group=workflow_group if isinstance(workflow_group, str) else None,
                workflow_field=workflow_field if isinstance(workflow_field, str) else None,
                final_path=final_path if isinstance(final_path, str) else None,
            )
        )
    return diagnostics


def _missing_relationship_metadata_diagnostics(
    final_output: typing.Mapping[str, typing.Any],
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]],
) -> typing.List[CustomOutputDiagnostic]:
    if not isinstance(workflow_extract, typing.Mapping):
        return []

    diagnostics: typing.List[CustomOutputDiagnostic] = []
    for group_name, group_spec in _relationship_intent_group_specs(workflow_extract):
        if not isinstance(group_spec, typing.Mapping):
            continue
        if not _group_requires_relationship_metadata(group_spec):
            continue
        group_output = final_output.get(group_name)
        if not isinstance(group_output, list) or len(group_output) == 0:
            continue
        diagnostics.append(
            CustomOutputDiagnostic(
                code="missing_output_relationships",
                message=(
                    f"workflow group [{group_name}] requires output relationship "
                    "metadata but no output_relationships were provided"
                ),
                workflow_group=group_name,
            )
        )
    return diagnostics


def _relationship_intent_group_specs(
    workflow_extract: typing.Mapping[str, typing.Any],
) -> typing.Iterator[typing.Tuple[str, typing.Any]]:
    seen: typing.Set[str] = set()
    for container_key in (
        "_groundx_persisted_extract",
        "groups",
        "prepared_final_groups",
    ):
        container = workflow_extract.get(container_key)
        if not isinstance(container, typing.Mapping):
            continue
        for group_name, group_spec in container.items():
            if isinstance(group_name, str) and group_name not in seen:
                seen.add(group_name)
                yield group_name, group_spec

    for group_name, group_spec in workflow_extract.items():
        if group_name in {
            "_groundx_persisted_extract",
            "groups",
            "prepared_final_groups",
            "workflow",
        }:
            continue
        if isinstance(group_name, str) and group_name not in seen:
            seen.add(group_name)
            yield group_name, group_spec


def _group_requires_relationship_metadata(
    group_spec: typing.Mapping[str, typing.Any],
) -> bool:
    match_attrs = group_spec.get("match_attrs")
    if isinstance(match_attrs, list) and len(match_attrs) > 0:
        return True
    passthrough = group_spec.get("passthrough")
    if isinstance(passthrough, typing.Mapping) and isinstance(
        passthrough.get("from"),
        str,
    ):
        return True
    return False


def _route_is_required(
    route: typing.Mapping[str, typing.Any],
    workflow_extract: typing.Mapping[str, typing.Any],
) -> bool:
    workflow_group = route.get("workflow_group")
    workflow_field = route.get("workflow_field")
    if isinstance(workflow_group, str) and isinstance(workflow_field, str):
        if _field_spec_required(workflow_extract, workflow_group, (workflow_field,)):
            return True

    final_path = route.get("final_path")
    if isinstance(final_path, str):
        parts = _pointer_parts(final_path)
        if len(parts) >= 2:
            return _field_spec_required(workflow_extract, parts[0], parts[1:])
    return False


def _field_spec_required(
    workflow_extract: typing.Mapping[str, typing.Any],
    group_name: str,
    field_path: typing.Sequence[str],
) -> bool:
    group_spec = _group_spec(workflow_extract, group_name)
    if not isinstance(group_spec, typing.Mapping):
        return False

    field_spec = _field_spec_at_path(group_spec, field_path)
    return _spec_required(field_spec)


def _group_spec(
    workflow_extract: typing.Mapping[str, typing.Any],
    group_name: str,
) -> typing.Any:
    for container_key in (
        "_groundx_persisted_extract",
        "groups",
        "prepared_final_groups",
    ):
        container = workflow_extract.get(container_key)
        if isinstance(container, typing.Mapping):
            group_spec = container.get(group_name)
            if group_spec is not None:
                return group_spec

    group_spec = workflow_extract.get(group_name)
    if isinstance(group_spec, typing.Mapping) and isinstance(
        group_spec.get("fields"),
        typing.Mapping,
    ):
        return group_spec
    return None


def _field_spec_at_path(
    group_spec: typing.Mapping[str, typing.Any],
    field_path: typing.Sequence[str],
) -> typing.Any:
    if not field_path:
        return None
    fields = group_spec.get("fields")
    if not isinstance(fields, typing.Mapping):
        return None

    field_name = field_path[0]
    field_spec = fields.get(field_name)
    if len(field_path) == 1:
        return field_spec

    if len(field_path) >= 3 and field_path[1] == "*":
        item_spec = field_spec[0] if isinstance(field_spec, list) and field_spec else field_spec
        if isinstance(item_spec, typing.Mapping):
            return _field_spec_at_path(
                typing.cast(typing.Mapping[str, typing.Any], item_spec),
                field_path[2:],
            )
    return None


def _spec_required(field_spec: typing.Any) -> bool:
    if not isinstance(field_spec, typing.Mapping):
        return False
    required = field_spec.get("required")
    if isinstance(required, bool):
        return required
    prompt = field_spec.get("prompt")
    if isinstance(prompt, typing.Mapping):
        prompt_required = prompt.get("required")
        if isinstance(prompt_required, bool):
            return prompt_required
    return False


def _pointer_parts(pointer: str) -> typing.Tuple[str, ...]:
    if not pointer.startswith("/"):
        return ()
    return tuple(_decode_pointer_part(part) for part in pointer.split("/")[1:] if part)


def _decode_pointer_part(part: str) -> str:
    return part.replace("~1", "/").replace("~0", "~")


def _encode_pointer(parts: typing.Sequence[str]) -> str:
    return "/" + "/".join(part.replace("~", "~0").replace("/", "~1") for part in parts)


def _apply_relationships(
    final_output: typing.Mapping[str, typing.Any],
    relationships: typing.Sequence[typing.Any],
    *,
    diagnostics: typing.Optional[typing.List[CustomOutputDiagnostic]] = None,
) -> typing.Tuple[typing.Dict[str, typing.Any], typing.List[CustomOutputDiagnostic]]:
    result = copy.deepcopy(dict(final_output))
    diagnostics = diagnostics or []

    for relationship in _relationship_application_order(relationships):
        if not isinstance(relationship, typing.Mapping):
            continue
        rel = typing.cast(typing.Mapping[str, typing.Any], relationship)
        rel_name = _relationship_name(rel)
        parent_group = rel.get("parent_group")
        child_group = rel.get("child_group")
        parent_output_field = rel.get("parent_output_field")
        match_attrs = rel.get("match_attrs")
        unmatched_child_group = rel.get("unmatched_child_group")
        if not (
            isinstance(parent_group, str)
            and isinstance(child_group, str)
            and isinstance(parent_output_field, str)
            and isinstance(match_attrs, list)
        ):
            diagnostics.append(
                CustomOutputDiagnostic(
                    code="invalid_relationship",
                    message=f"relationship {rel_name} is missing required metadata",
                    relationship=rel_name,
                )
            )
            continue

        if parent_group not in result:
            result[parent_group] = []
        if child_group not in result:
            result[child_group] = []

        parent_records = result.get(parent_group)
        child_records = result.get(child_group)
        if not _is_mapping_list(parent_records) or not _is_mapping_list(child_records):
            diagnostics.append(
                CustomOutputDiagnostic(
                    code="invalid_relationship_output",
                    message=(f"relationship {rel_name} requires list outputs for {parent_group} and {child_group}"),
                    relationship=rel_name,
                )
            )
            continue

        parent_list = typing.cast(
            typing.List[typing.Dict[str, typing.Any]],
            parent_records,
        )
        child_list = typing.cast(
            typing.List[typing.Dict[str, typing.Any]],
            child_records,
        )
        for parent in parent_list:
            parent.setdefault(parent_output_field, [])

        unmatched: typing.List[typing.Dict[str, typing.Any]] = []
        for child_index, child in enumerate(child_list):
            # Task 3.2a7b: every parent selection is delegated to the one
            # exported primitive, resolved as a module global so the
            # delegation is observable and monkeypatchable.
            selection = select_relationship_parent(parent_list, child, rel)
            if selection.ambiguous:
                diagnostics.append(
                    CustomOutputDiagnostic(
                        code="ambiguous_relationship_match",
                        message=(f"relationship {rel_name} child record {child_index} matches more than one parent"),
                        severity="warning",
                        relationship=rel_name,
                        child_record_index=child_index,
                    )
                )
                unmatched.append(child)
                continue
            selected_parent = selection.parent
            if isinstance(selected_parent, dict):
                output = selected_parent.setdefault(parent_output_field, [])
                if isinstance(output, list):
                    output.append(copy.deepcopy(child))
                continue
            unmatched.append(child)

        result.pop(child_group, None)
        if isinstance(unmatched_child_group, str) and unmatched:
            result[unmatched_child_group] = unmatched
        elif isinstance(unmatched_child_group, str):
            result.setdefault(unmatched_child_group, [])

    return result, diagnostics


def _record_repeated_group_path(
    repeated_group_paths: typing.Dict[
        str,
        typing.Set[typing.Tuple[str, ...]],
    ],
    pointer: str,
) -> None:
    parts = _pointer_parts(pointer)
    if "*" not in parts:
        return
    if not parts:
        return
    final_group = parts[0]
    repeated_path = parts[: parts.index("*")]
    if repeated_path:
        repeated_group_paths.setdefault(final_group, set()).add(repeated_path)


def _dedupe_repeated_group_outputs(
    final_output: typing.Dict[str, typing.Any],
    repeated_group_paths: typing.Mapping[
        str,
        typing.Set[typing.Tuple[str, ...]],
    ],
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]],
) -> None:
    for workflow_group, paths in repeated_group_paths.items():
        unique_attrs, identity_match = _group_identity_policy(
            workflow_extract,
            workflow_group,
        )
        if not unique_attrs:
            continue
        for path in paths:
            records = _value_at_path(final_output, path)
            if not _is_mapping_list(records):
                continue
            record_list = typing.cast(
                typing.List[typing.Dict[str, typing.Any]],
                records,
            )
            record_list[:] = _dedupe_repeated_records(
                record_list,
                unique_attrs,
                identity_match,
            )


def _value_at_path(
    output: typing.Mapping[str, typing.Any],
    path: typing.Sequence[str],
) -> typing.Any:
    value: typing.Any = output
    for part in path:
        if not isinstance(value, typing.Mapping):
            return None
        value = value.get(part)
    return value


def _dedupe_repeated_records(
    records: typing.List[typing.Dict[str, typing.Any]],
    unique_attrs: typing.Sequence[str],
    identity_match: typing.Optional[typing.Mapping[str, typing.Any]] = None,
) -> typing.List[typing.Dict[str, typing.Any]]:
    if not unique_attrs:
        return records

    if identity_match is not None:
        deduped: typing.List[typing.Dict[str, typing.Any]] = []
        exact_attrs = _identity_exact_attrs(identity_match, unique_attrs)
        threshold_attrs = set(
            _unique_strings(
                typing.cast(
                    typing.Iterable[typing.Any],
                    identity_match.get("threshold_attrs", []),
                )
            )
        )
        fixed_attrs = tuple(attr for attr in unique_attrs if attr not in threshold_attrs)
        indexes_by_fixed_identity: typing.Dict[
            typing.Tuple[typing.Tuple[str, typing.Any], ...],
            _AdvancedIdentityIndex,
        ] = {}
        for record in records:
            fixed_identity = _identity_partition_key(
                record,
                fixed_attrs,
                exact_attrs,
            )
            index = indexes_by_fixed_identity.get(fixed_identity)
            if index is None:
                index = _AdvancedIdentityIndex(identity_match, unique_attrs)
                indexes_by_fixed_identity[fixed_identity] = index
            match = index.first_match(record, unique_attrs)
            if match is None:
                deduped.append(record)
                index.add(record)
            else:
                existing_index, existing = match
                _merge_identity_record(existing, record)
                index.refresh(existing_index)
        return deduped

    exact_deduped: typing.List[typing.Dict[str, typing.Any]] = []
    by_key: typing.Dict[
        typing.Tuple[typing.Tuple[str, typing.Any], ...],
        typing.Dict[str, typing.Any],
    ] = {}
    for record in records:
        identity_key = _identity_key(record, unique_attrs)
        if identity_key is None:
            exact_deduped.append(record)
            continue
        exact_existing = by_key.get(identity_key)
        if exact_existing is None:
            by_key[identity_key] = record
            exact_deduped.append(record)
            continue
        _merge_identity_record(exact_existing, record)
    return exact_deduped


class _AdvancedIdentityIndex:
    def __init__(
        self,
        identity_match: typing.Mapping[str, typing.Any],
        unique_attrs: typing.Sequence[str],
    ) -> None:
        self.identity_match = identity_match
        self.threshold_attrs = _unique_strings(
            typing.cast(
                typing.Iterable[typing.Any],
                identity_match.get("threshold_attrs", []),
            )
        )
        self.activate_threshold_at = _identity_threshold(
            identity_match,
            "activate_threshold_at",
        )
        self.minimum_threshold_matches = _identity_threshold(
            identity_match,
            "minimum_threshold_matches",
        )
        self.exact_attrs = _identity_exact_attrs(identity_match, unique_attrs)
        self.records: typing.List[typing.Dict[str, typing.Any]] = []
        self.presence_bits = {attr: 0 for attr in self.threshold_attrs}
        self.value_bits: typing.Dict[str, typing.Dict[typing.Any, int]] = {attr: {} for attr in self.threshold_attrs}
        self.indexed_values: typing.List[typing.Dict[str, typing.Tuple[bool, typing.Any]]] = []
        shortcuts = identity_match.get("equal_value_shortcuts", {})
        shortcut_map = (
            typing.cast(typing.Mapping[str, typing.Any], shortcuts) if isinstance(shortcuts, typing.Mapping) else {}
        )
        self.shortcut_values = {
            attr: {
                _identity_index_value(value, exact=attr in self.exact_attrs)
                for value in typing.cast(typing.Iterable[typing.Any], values)
            }
            for attr, values in shortcut_map.items()
            if isinstance(values, list)
        }

    def add(self, record: typing.Dict[str, typing.Any]) -> None:
        index = len(self.records)
        self.records.append(record)
        self.indexed_values.append({})
        self._index(index)

    def refresh(self, index: int) -> None:
        bit = 1 << index
        for attr, (present, value_key) in self.indexed_values[index].items():
            if present:
                self.presence_bits[attr] &= ~bit
            value_index = self.value_bits[attr]
            remaining = value_index[value_key] & ~bit
            if remaining:
                value_index[value_key] = remaining
            else:
                del value_index[value_key]
        self.indexed_values[index] = {}
        self._index(index)

    def first_match(
        self,
        record: typing.Mapping[str, typing.Any],
        unique_attrs: typing.Sequence[str],
    ) -> typing.Optional[typing.Tuple[int, typing.Dict[str, typing.Any]]]:
        candidates = self._candidate_bits(record)
        while candidates:
            candidate_bit = candidates & -candidates
            candidate_index = candidate_bit.bit_length() - 1
            candidate = self.records[candidate_index]
            if _records_share_identity(
                candidate,
                record,
                unique_attrs,
                self.identity_match,
            ):
                return candidate_index, candidate
            candidates ^= candidate_bit
        return None

    def _index(self, index: int) -> None:
        record = self.records[index]
        bit = 1 << index
        indexed_values: typing.Dict[str, typing.Tuple[bool, typing.Any]] = {}
        for attr in self.threshold_attrs:
            present = attr in record
            value_key = _identity_index_value(
                record.get(attr),
                exact=attr in self.exact_attrs,
            )
            indexed_values[attr] = present, value_key
            if present:
                self.presence_bits[attr] |= bit
            attr_values = self.value_bits[attr]
            attr_values[value_key] = attr_values.get(value_key, 0) | bit
        self.indexed_values[index] = indexed_values

    def _candidate_bits(self, record: typing.Mapping[str, typing.Any]) -> int:
        universe = (1 << len(self.records)) - 1
        if not universe:
            return 0

        equality_bits: typing.List[int] = []
        shortcut_bits = 0
        present_attrs: typing.Set[str] = set()
        for attr in self.threshold_attrs:
            present = attr in record
            if present:
                present_attrs.add(attr)
            value_key = _identity_index_value(
                record.get(attr),
                exact=attr in self.exact_attrs,
            )
            equal = self.value_bits[attr].get(value_key, 0)
            if not present:
                equal &= self.presence_bits[attr]
            equality_bits.append(equal)
            if present and value_key in self.shortcut_values.get(attr, set()):
                shortcut_bits |= equal & self.presence_bits[attr]

        threshold_bits = _at_least_count_bits(
            equality_bits,
            self.minimum_threshold_matches,
            universe,
        )
        remaining_presence_limit = self.activate_threshold_at - len(present_attrs) - 1
        underactivation_bits = _at_most_count_bits(
            [self.presence_bits[attr] for attr in self.threshold_attrs if attr not in present_attrs],
            remaining_presence_limit,
            universe,
        )
        return shortcut_bits | threshold_bits | underactivation_bits


def _at_least_count_bits(
    value_bits: typing.Sequence[int],
    minimum: int,
    universe: int,
) -> int:
    if minimum <= 0:
        return universe
    if minimum > len(value_bits):
        return 0
    at_least = [universe, *([0] * minimum)]
    for bits in value_bits:
        for count in range(minimum, 0, -1):
            at_least[count] |= at_least[count - 1] & bits
    return at_least[minimum]


def _at_most_count_bits(
    value_bits: typing.Sequence[int],
    maximum: int,
    universe: int,
) -> int:
    if maximum < 0:
        return 0
    if maximum >= len(value_bits):
        return universe
    exact = [universe, *([0] * maximum)]
    for bits in value_bits:
        without_bits = universe ^ bits
        next_exact = [0] * (maximum + 1)
        next_exact[0] = exact[0] & without_bits
        for count in range(1, maximum + 1):
            next_exact[count] = (exact[count] & without_bits) | (exact[count - 1] & bits)
        exact = next_exact
    result = 0
    for bits in exact:
        result |= bits
    return result


def _identity_index_value(value: typing.Any, *, exact: bool = False) -> typing.Any:
    if _match_value_absent(value):
        return ("absent",)
    return ("value", _hashable_identity_value(value, exact=exact))


def _records_share_identity(
    first: typing.Mapping[str, typing.Any],
    second: typing.Mapping[str, typing.Any],
    unique_attrs: typing.Sequence[str],
    identity_match: typing.Mapping[str, typing.Any],
) -> bool:
    threshold_attrs = _unique_strings(
        typing.cast(typing.Iterable[typing.Any], identity_match.get("threshold_attrs", []))
    )
    threshold_attr_set = set(threshold_attrs)
    exact_attrs = _identity_exact_attrs(identity_match, unique_attrs)
    for attr in unique_attrs:
        if attr in threshold_attr_set:
            continue
        if not _identity_values_match(
            first.get(attr),
            second.get(attr),
            match_absent=True,
            exact=attr in exact_attrs,
        ):
            return False

    shortcuts_value = identity_match.get("equal_value_shortcuts", {})
    shortcuts = (
        typing.cast(typing.Mapping[str, typing.Any], shortcuts_value)
        if isinstance(shortcuts_value, typing.Mapping)
        else {}
    )
    threshold_values = 0
    threshold_matches = 0
    for attr in threshold_attrs:
        first_value = first.get(attr)
        second_value = second.get(attr)
        first_present = attr in first
        second_present = attr in second
        if first_present or second_present:
            threshold_values += 1
        if (first_present or second_present) and _identity_values_match(
            first_value,
            second_value,
            match_absent=True,
            exact=attr in exact_attrs,
        ):
            threshold_matches += 1

        shortcut_values = shortcuts.get(attr, [])
        if (
            isinstance(shortcut_values, list)
            and first_present
            and second_present
            and _identity_comparison_value(
                first_value,
                exact=attr in exact_attrs,
            )
            == _identity_comparison_value(
                second_value,
                exact=attr in exact_attrs,
            )
            and any(
                _identity_comparison_value(
                    first_value,
                    exact=attr in exact_attrs,
                )
                == _identity_comparison_value(
                    shortcut,
                    exact=attr in exact_attrs,
                )
                for shortcut in shortcut_values
            )
        ):
            return True

    activate_threshold_at = _identity_threshold(
        identity_match,
        "activate_threshold_at",
    )
    minimum_threshold_matches = _identity_threshold(
        identity_match,
        "minimum_threshold_matches",
    )
    return not (threshold_values >= activate_threshold_at and threshold_matches < minimum_threshold_matches)


def _identity_values_match(
    first: typing.Any,
    second: typing.Any,
    *,
    match_absent: bool,
    exact: bool = False,
) -> bool:
    first_absent = _match_value_absent(first)
    second_absent = _match_value_absent(second)
    if first_absent or second_absent:
        return match_absent and first_absent and second_absent
    first_unwrapped = _unwrap_match_value(first)
    second_unwrapped = _unwrap_match_value(second)
    if isinstance(first_unwrapped, str) and isinstance(second_unwrapped, str):
        return values_match(first_unwrapped, second_unwrapped)
    return _identity_comparison_value(
        first,
        exact=exact,
    ) == _identity_comparison_value(second, exact=exact)


def _identity_key(
    record: typing.Mapping[str, typing.Any],
    unique_attrs: typing.Sequence[str],
    exact_attrs: typing.AbstractSet[str] = frozenset(),
) -> typing.Optional[typing.Tuple[typing.Tuple[str, typing.Any], ...]]:
    values: typing.List[typing.Tuple[str, typing.Any]] = []
    for attr in unique_attrs:
        raw = record.get(attr)
        if _match_value_absent(raw):
            return None
        values.append(
            (
                attr,
                _hashable_identity_value(raw, exact=attr in exact_attrs),
            )
        )
    return tuple(values)


def _identity_partition_key(
    record: typing.Mapping[str, typing.Any],
    attrs: typing.Sequence[str],
    exact_attrs: typing.AbstractSet[str] = frozenset(),
) -> typing.Tuple[typing.Tuple[str, typing.Any], ...]:
    return tuple(
        (
            attr,
            ("absent",)
            if _match_value_absent(record.get(attr))
            else (
                "value",
                _hashable_identity_value(
                    record.get(attr),
                    exact=attr in exact_attrs,
                ),
            ),
        )
        for attr in attrs
    )


def _hashable_identity_value(value: typing.Any, *, exact: bool = False) -> typing.Any:
    normalized = _identity_comparison_value(value, exact=exact)
    try:
        hash(normalized)
    except TypeError:
        return (
            "structured",
            type(normalized).__name__,
            _record_key(_plain(normalized)),
        )
    return normalized


def _identity_comparison_value(value: typing.Any, *, exact: bool) -> typing.Any:
    del exact
    return _normalize_match_value(value)


def _identity_exact_attrs(
    identity_match: typing.Mapping[str, typing.Any],
    unique_attrs: typing.Sequence[str],
) -> typing.FrozenSet[str]:
    configured = identity_match["exact_attrs"] if "exact_attrs" in identity_match else unique_attrs
    return frozenset(
        _unique_strings(
            typing.cast(typing.Iterable[typing.Any], configured),
        )
    )


def _identity_threshold(
    identity_match: typing.Mapping[str, typing.Any],
    key: str,
) -> int:
    value = identity_match.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"identity_match.{key} must be an integer")
    if value < 0:
        raise ValueError(f"identity_match.{key} must be non-negative")
    return value


def _group_identity_policy(
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]],
    group_name: str,
) -> typing.Tuple[
    typing.Tuple[str, ...],
    typing.Optional[typing.Mapping[str, typing.Any]],
]:
    if not isinstance(workflow_extract, typing.Mapping):
        return (), None

    group_spec = _group_spec(workflow_extract, group_name)
    if not isinstance(group_spec, typing.Mapping):
        return (), None

    unique_attrs = group_spec.get("unique_attrs")
    if not isinstance(unique_attrs, list) or not unique_attrs:
        return (), None

    identity_match = group_spec.get("identity_match")
    if isinstance(identity_match, typing.Mapping):
        _identity_threshold(identity_match, "activate_threshold_at")
        _identity_threshold(identity_match, "minimum_threshold_matches")
    return (
        _unique_strings(unique_attrs),
        typing.cast(typing.Mapping[str, typing.Any], identity_match)
        if isinstance(identity_match, typing.Mapping)
        else None,
    )


def _unique_strings(values: typing.Iterable[typing.Any]) -> typing.Tuple[str, ...]:
    seen: typing.Set[str] = set()
    result: typing.List[str] = []
    for value in values:
        if not isinstance(value, str) or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


def _merge_identity_record(
    target: typing.Dict[str, typing.Any],
    source: typing.Mapping[str, typing.Any],
) -> None:
    if isinstance(target, _LineagedRecord) and isinstance(source, _LineagedRecord):
        target.page_numbers = _merge_page_numbers(
            target.page_numbers,
            source.page_numbers,
        )
    for key, value in source.items():
        if key not in target or _match_value_absent(target.get(key)):
            target[key] = copy.deepcopy(value)
            continue
        target_value = target.get(key)
        if isinstance(target_value, dict) and isinstance(value, typing.Mapping):
            _merge_identity_record(
                target_value,
                typing.cast(typing.Mapping[str, typing.Any], value),
            )
            continue
        if isinstance(target_value, list) and isinstance(value, list):
            for item in value:
                if item not in target_value:
                    target_value.append(copy.deepcopy(item))


def _relationship_application_order(
    relationships: typing.Sequence[typing.Any],
) -> typing.List[typing.Any]:
    ordered: typing.List[typing.Any] = []
    visited: typing.Set[int] = set()
    visiting: typing.Set[int] = set()

    def visit(index: int) -> None:
        if index in visited:
            return
        if index in visiting:
            return
        visiting.add(index)
        relationship = relationships[index]
        if isinstance(relationship, typing.Mapping):
            child_group = relationship.get("child_group")
            if isinstance(child_group, str):
                for dependency_index, dependency in enumerate(relationships):
                    if dependency_index == index:
                        continue
                    if not isinstance(dependency, typing.Mapping):
                        continue
                    if dependency.get("parent_group") == child_group:
                        visit(dependency_index)
        visiting.remove(index)
        visited.add(index)
        ordered.append(relationship)

    for index in range(len(relationships)):
        visit(index)

    return ordered


def _relationship_name(relationship: typing.Mapping[str, typing.Any]) -> str:
    parent = relationship.get("parent_group")
    child = relationship.get("child_group")
    return f"{parent}->{child}"


def _is_mapping_list(value: typing.Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, dict) for item in value)


def _match_value_absent(value: typing.Any) -> bool:
    unwrapped = _unwrap_match_value(value)
    if unwrapped is None:
        return True
    if isinstance(unwrapped, str) and unwrapped.strip() == "":
        return True
    return False


def _relationship_packet_value(
    relationship: typing.Mapping[str, typing.Any],
    key: str,
) -> typing.Any:
    """Read a relationship packet field in either the persisted snake_case or
    the dispatched camelCase spelling (design.md:394-396)."""
    if key in relationship:
        return relationship[key]
    camel_key = _RELATIONSHIP_PACKET_CAMEL_KEYS.get(key)
    if camel_key is not None:
        return relationship.get(camel_key)
    return None


def _relationship_attr_list(value: typing.Any) -> typing.List[str]:
    if not isinstance(value, list):
        return []
    return [attr for attr in value if isinstance(attr, str) and attr != ""]


def _relationship_value_absent(value: typing.Any) -> bool:
    """Empty values count as absent for relationship matching.

    Ported from legacy `internal-arcadia classes/image_evidence.py:273-285`
    (`is_empty_source_value`), applied after unwrapping ExtractedField-style
    value mappings.
    """
    unwrapped = _unwrap_match_value(value)
    if unwrapped is None:
        return True
    if isinstance(unwrapped, str):
        return unwrapped.strip() == ""
    if isinstance(unwrapped, (list, tuple, set)):
        items = typing.cast(typing.Iterable[typing.Any], unwrapped)
        return all(_relationship_value_absent(item) for item in items)
    if isinstance(unwrapped, typing.Mapping):
        mapping = typing.cast(typing.Mapping[typing.Any, typing.Any], unwrapped)
        if not mapping:
            return True
        return all(_relationship_value_absent(item) for item in mapping.values())
    return False


def _relationship_comparison_value(value: typing.Any) -> typing.Any:
    """Normalize a match value for relationship comparison.

    Strings use the shared extraction identity key. Ints and floats compare as numbers, and
    differently-typed values never compare equal. Booleans stay distinct from
    numbers, and structured values compare structurally with the same string
    normalization.
    """
    unwrapped = _unwrap_match_value(value)
    if isinstance(unwrapped, bool):
        return ("boolean", unwrapped)
    if isinstance(unwrapped, numbers.Integral):
        return ("number", float(unwrapped))
    if isinstance(unwrapped, numbers.Real):
        return ("number", float(unwrapped))
    if isinstance(unwrapped, str):
        return ("string", match_key(unwrapped))
    if isinstance(unwrapped, typing.Mapping):
        mapping = typing.cast(typing.Mapping[typing.Any, typing.Any], unwrapped)
        return (
            "object",
            tuple(
                sorted(
                    (
                        str(key),
                        _relationship_comparison_value(item),
                    )
                    for key, item in mapping.items()
                )
            ),
        )
    if isinstance(unwrapped, (list, tuple)):
        return (
            "list",
            tuple(_relationship_comparison_value(item) for item in unwrapped),
        )
    return unwrapped


def _normalize_match_value(value: typing.Any) -> typing.Any:
    unwrapped = _unwrap_match_value(value)
    if isinstance(unwrapped, str):
        return match_key(unwrapped)
    if isinstance(unwrapped, bool):
        return ("boolean", unwrapped)
    if isinstance(unwrapped, numbers.Integral):
        return ("number", int(unwrapped))
    if isinstance(unwrapped, numbers.Real):
        numeric = float(unwrapped)
        if numeric.is_integer():
            return ("number", int(numeric))
        return ("float", numeric)
    if isinstance(unwrapped, typing.Mapping):
        return (
            "object",
            tuple(
                sorted(
                    (
                        str(key),
                        _normalize_match_value(item),
                    )
                    for key, item in unwrapped.items()
                )
            ),
        )
    if isinstance(unwrapped, (list, tuple)):
        return (
            "list",
            tuple(_normalize_match_value(item) for item in unwrapped),
        )
    return unwrapped


def _unwrap_match_value(value: typing.Any) -> typing.Any:
    if isinstance(value, typing.Mapping):
        value_map = typing.cast(typing.Mapping[str, typing.Any], value)
        if "value" in value_map and set(value_map.keys()).issubset(_EXTRACTED_FIELD_VALUE_KEYS):
            return value_map.get("value")
    return value


def _record_key(value: typing.Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)
