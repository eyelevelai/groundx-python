from __future__ import annotations

import copy
import dataclasses
import json
import numbers
import typing

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
class CustomOutputReassemblyResult:
    final_output: typing.Dict[str, typing.Any]
    relationship_output: typing.Optional[typing.Dict[str, typing.Any]]
    diagnostics: typing.List[CustomOutputDiagnostic]
    workflow_output: typing.Dict[str, typing.Any] = dataclasses.field(
        default_factory=dict
    )
    source_provenance: typing.List[CustomOutputSourceProvenance] = (
        dataclasses.field(default_factory=list)
    )


@dataclasses.dataclass(frozen=True)
class _RouteValue:
    value: typing.Any
    record_index: typing.Optional[int]
    repeated: bool


@dataclasses.dataclass(frozen=True)
class _RouteContainer:
    identity: typing.Tuple[typing.Any, ...]
    value: typing.Any
    page_numbers: typing.Tuple[int, ...] = ()


_REPEATED_STEP_KINDS = {"keys", "summary"}
_EXTRACTED_FIELD_VALUE_KEYS = {"value", "confidence", "conflicts", "qa"}
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
    route_hits: typing.Dict[int, bool] = {}
    repeated_records: typing.Dict[
        typing.Tuple[typing.Tuple[str, ...], typing.Tuple[typing.Any, ...]],
        typing.Dict[str, typing.Any],
    ] = {}
    workflow_repeated_records: typing.Dict[
        typing.Tuple[str, typing.Tuple[typing.Any, ...]],
        typing.Dict[str, typing.Any],
    ] = {}

    for route_index, route in enumerate(routes):
        route_hits[route_index] = False
        if not isinstance(route, dict):
            continue
        route_map = typing.cast(typing.Mapping[str, typing.Any], route)
        final_path = route_map.get("final_path")
        if not isinstance(final_path, str):
            continue

        for route_container in _route_containers(xray, route_map):
            for route_value in _custom_route_values(
                route_container.value,
                route_map,
                step_kinds=step_kinds,
            ):
                if _is_empty_output(route_value.value):
                    continue
                route_hits[route_index] = True
                pointer = _effective_pointer(final_path, repeated=route_value.repeated)
                record_key = (
                    *route_container.identity,
                    route_map.get("step_name"),
                    route_value.record_index,
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
                )

    relationships = workflow.get("output_relationships") if workflow else None
    relationship_output = None
    diagnostics = _missing_required_route_diagnostics(
        typing.cast(typing.Sequence[typing.Any], routes),
        route_hits,
        workflow_extract,
    )
    if isinstance(relationships, list) and relationships:
        relationship_output, diagnostics = _apply_relationships(
            final_output,
            typing.cast(typing.Sequence[typing.Any], relationships),
            diagnostics=diagnostics,
        )
        final_output = copy.deepcopy(relationship_output)

    return CustomOutputReassemblyResult(
        final_output=final_output,
        relationship_output=relationship_output,
        diagnostics=diagnostics,
        workflow_output=workflow_output,
        source_provenance=source_provenance,
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
        return _record_key(
            (output_map_name, "payload_pages", payload_identity, page_numbers)
        )
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


def _route_containers(
    xray: typing.Any,
    route: typing.Mapping[str, typing.Any],
) -> typing.List[_RouteContainer]:
    level = route.get("level")
    output_map_name = route.get("output_map")
    if level == "document":
        if not isinstance(output_map_name, str):
            return [_RouteContainer(identity=("document",), value=xray)]
        document_containers: typing.List[_RouteContainer] = []
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

    step_value = output_map.get(step_name)
    is_repeated_step = step_kinds.get(step_name) in _REPEATED_STEP_KINDS

    if isinstance(step_value, typing.Mapping):
        records = step_value.get("_records")
        if isinstance(records, list):
            record_values: typing.List[_RouteValue] = []
            for index, record in enumerate(records):
                if not isinstance(record, typing.Mapping) or output_key not in record:
                    continue
                record_values.append(
                    _RouteValue(
                        value=record[output_key],
                        record_index=index,
                        repeated=True,
                    )
                )
            if record_values:
                return record_values

        if output_key not in step_value:
            return []
        value = step_value[output_key]
        if isinstance(value, list):
            return [
                _RouteValue(value=item, record_index=index, repeated=True)
                for index, item in enumerate(value)
            ]
        return [
            _RouteValue(
                value=value,
                record_index=0 if is_repeated_step else None,
                repeated=is_repeated_step and not isinstance(records, list),
            )
        ]

    if isinstance(step_value, list):
        values: typing.List[_RouteValue] = []
        for index, record in enumerate(step_value):
            if isinstance(record, typing.Mapping):
                if output_key not in record:
                    continue
                values.append(
                    _RouteValue(
                        value=record[output_key],
                        record_index=index,
                        repeated=True,
                    )
                )
            else:
                values.append(
                    _RouteValue(value=record, record_index=index, repeated=True)
                )
        return values

    if step_value is None:
        return []
    return [
        _RouteValue(
            value=step_value,
            record_index=0 if is_repeated_step else None,
            repeated=is_repeated_step,
        )
    ]


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


def _effective_pointer(pointer: str, *, repeated: bool) -> str:
    if not repeated or "*" in pointer:
        return pointer
    parts = _pointer_parts(pointer)
    if len(parts) < 2:
        return pointer
    return _encode_pointer((*parts[:-1], "*", parts[-1]))


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
            record = {}
            repeated_records[item_key] = record
            records.append(record)

        field_path = parts[star_index + 1 :]
        if field_path:
            _set_nested_value(record, field_path, value)
        return

    current = result
    for part in parts[:-1]:
        next_value = current.setdefault(part, {})
        if not isinstance(next_value, dict):
            return
        current = next_value
    current[parts[-1]] = value


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
    route_hits: typing.Mapping[int, bool],
    workflow_extract: typing.Optional[typing.Mapping[str, typing.Any]],
) -> typing.List[CustomOutputDiagnostic]:
    if not isinstance(workflow_extract, typing.Mapping):
        return []

    hit_workflow_groups = {
        str(route.get("workflow_group"))
        for index, route in enumerate(routes)
        if route_hits.get(index) and isinstance(route, typing.Mapping)
    }
    diagnostics: typing.List[CustomOutputDiagnostic] = []
    for index, route in enumerate(routes):
        if route_hits.get(index):
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
            if isinstance(workflow_group, str)
            and workflow_group not in hit_workflow_groups
            else "missing_workflow_field"
        )
        diagnostics.append(
            CustomOutputDiagnostic(
                code=code,
                message=(
                    f"required workflow output [{workflow_group}.{workflow_field}] "
                    f"for [{final_path}] is missing"
                ),
                workflow_group=workflow_group if isinstance(workflow_group, str) else None,
                workflow_field=workflow_field if isinstance(workflow_field, str) else None,
                final_path=final_path if isinstance(final_path, str) else None,
            )
        )
    return diagnostics


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
    for container_key in ("groups", "prepared_final_groups"):
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
        item_spec = (
            field_spec[0]
            if isinstance(field_spec, list) and field_spec
            else field_spec
        )
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
    return "/" + "/".join(
        part.replace("~", "~0").replace("/", "~1") for part in parts
    )


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
                    message=(
                        f"relationship {rel_name} requires list outputs for "
                        f"{parent_group} and {child_group}"
                    ),
                    relationship=rel_name,
                )
            )
            continue

        parent_list = _dedupe_relationship_parents(
            typing.cast(typing.List[typing.Dict[str, typing.Any]], parent_records),
            typing.cast(typing.List[str], match_attrs),
        )
        result[parent_group] = parent_list
        child_list = typing.cast(typing.List[typing.Dict[str, typing.Any]], child_records)
        for parent in parent_list:
            parent.setdefault(parent_output_field, [])

        unmatched: typing.List[typing.Dict[str, typing.Any]] = []
        for child_index, child in enumerate(child_list):
            matches = [
                parent
                for parent in parent_list
                if _records_match(parent, child, typing.cast(typing.List[str], match_attrs))
            ]
            if len(matches) > 1:
                diagnostics.append(
                    CustomOutputDiagnostic(
                        code="ambiguous_relationship_match",
                        message=(
                            f"relationship {rel_name} child record {child_index} "
                            "matches more than one parent"
                        ),
                        # Ambiguity is a HANDLED data condition: the child is
                        # routed to the unmatched group (rendered account-level
                        # per the relationship algorithm), so it must not fail
                        # the document. Live prod 2026-07-08: a real utility
                        # bill whose meters share match-attr values failed
                        # entirely under the default severity="error".
                        severity="warning",
                        relationship=rel_name,
                        child_record_index=child_index,
                    )
                )
                unmatched.append(child)
                continue
            if len(matches) == 1:
                output = matches[0].setdefault(parent_output_field, [])
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


def _dedupe_relationship_parents(
    parent_list: typing.List[typing.Dict[str, typing.Any]],
    match_attrs: typing.Sequence[str],
) -> typing.List[typing.Dict[str, typing.Any]]:
    deduped: typing.List[typing.Dict[str, typing.Any]] = []
    by_key: typing.Dict[
        typing.Tuple[typing.Tuple[str, typing.Any], ...],
        typing.Dict[str, typing.Any],
    ] = {}
    for parent in parent_list:
        parent_key = _match_key(parent, match_attrs)
        if not parent_key:
            deduped.append(parent)
            continue
        existing = by_key.get(parent_key)
        if existing is None:
            by_key[parent_key] = parent
            deduped.append(parent)
            continue
        _merge_relationship_parent(existing, parent)
    return deduped


def _merge_relationship_parent(
    target: typing.Dict[str, typing.Any],
    source: typing.Mapping[str, typing.Any],
) -> None:
    for key, value in source.items():
        if key not in target or _match_value_absent(target.get(key)):
            target[key] = copy.deepcopy(value)
            continue
        target_value = target.get(key)
        if isinstance(target_value, dict) and isinstance(value, typing.Mapping):
            _merge_relationship_parent(
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


def _records_match(
    parent: typing.Mapping[str, typing.Any],
    child: typing.Mapping[str, typing.Any],
    match_attrs: typing.Sequence[str],
) -> bool:
    parent_key = _match_key(parent, match_attrs)
    child_key = _match_key(child, match_attrs)
    if not parent_key or not child_key:
        return False
    return parent_key == child_key


def _match_key(
    record: typing.Mapping[str, typing.Any],
    match_attrs: typing.Sequence[str],
) -> typing.Tuple[typing.Tuple[str, typing.Any], ...]:
    values: typing.List[typing.Tuple[str, typing.Any]] = []
    for attr in match_attrs:
        raw = record.get(attr)
        if _match_value_absent(raw):
            continue
        values.append((attr, _normalize_match_value(raw)))
    return tuple(values)


def _match_value_absent(value: typing.Any) -> bool:
    unwrapped = _unwrap_match_value(value)
    if unwrapped is None:
        return True
    if isinstance(unwrapped, str) and unwrapped.strip() == "":
        return True
    return False


def _normalize_match_value(value: typing.Any) -> typing.Any:
    unwrapped = _unwrap_match_value(value)
    if isinstance(unwrapped, str):
        return unwrapped.strip().casefold()
    if isinstance(unwrapped, numbers.Real):
        return float(unwrapped)
    return unwrapped


def _unwrap_match_value(value: typing.Any) -> typing.Any:
    if isinstance(value, typing.Mapping):
        value_map = typing.cast(typing.Mapping[str, typing.Any], value)
        if "value" in value_map and set(value_map.keys()).issubset(
            _EXTRACTED_FIELD_VALUE_KEYS
        ):
            return value_map.get("value")
    return value


def _record_key(value: typing.Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)
