import collections.abc
import copy
import dataclasses
import hashlib
import json
import re
import typing

import yaml
from ..classes.element import Element
from ..classes.field import ExtractedField
from ..classes.group import Group
from ..classes.prompt import Prompt

_PERSISTED_WORKFLOW_EXTRACT_KEY = "_groundx_persisted_extract"
_CUSTOM_WORKFLOW_KEY = "workflow"
_CUSTOM_WORKFLOW_GROUP_METADATA_KEY = "workflow_step"
_CUSTOM_WORKFLOW_FIELD_METADATA_KEY = "workflow_output_key"
_CUSTOM_WORKFLOW_METADATA_VERSION = 1
_CUSTOM_WORKFLOW_MAX_FIELDS = 30
_CUSTOM_WORKFLOW_AGENT_CHAIN_KEY = "agent_chain"
_CUSTOM_WORKFLOW_OUTPUT_MAPS = {
    "chunk": "customChunkOutputs",
    "section": "customSectionOutputs",
    "document": "customDocumentOutputs",
}
_CUSTOM_WORKFLOW_AGENT_CHAIN_AGENT_TASKS = frozenset(
    {
        "reconcile_charges",
        "reconcile_meters",
        "reconcile_statement",
        "qa_meters",
        "qa_statement",
    }
)
_CUSTOM_WORKFLOW_AGENT_CHAIN_SAVE_TASKS = frozenset(
    {
        "save_charges",
        "save_meters",
        "save_statement",
    }
)
_CUSTOM_WORKFLOW_AGENT_CHAIN_SUPPORTED_TASKS = (
    _CUSTOM_WORKFLOW_AGENT_CHAIN_AGENT_TASKS | _CUSTOM_WORKFLOW_AGENT_CHAIN_SAVE_TASKS
)
_RESERVED_TOP_LEVEL_KEYS = {
    "_defs",
    "_pseudo_groups",
    _PERSISTED_WORKFLOW_EXTRACT_KEY,
    _CUSTOM_WORKFLOW_KEY,
}
_EXTRACTION_POLICY_VERSION_KEY = "extraction_policy_version"
_SUPPORTED_TOP_LEVEL_METADATA_KEYS = {_EXTRACTION_POLICY_VERSION_KEY}
_SUPPORTED_FINAL_GROUP_METADATA_KEYS = {
    "always_check_attrs",
    "conflict_attrs",
    "deregulation_status_values",
    "equivalent_service_types",
    "exclude_dict_attrs",
    "explanation_attrs",
    "fill_rules",
    "final_value_aliases",
    "match_attrs",
    "not_required_service_types",
    "partial_pair_attrs",
    "passthrough",
    "passthrough_attrs",
    "passthrough_pair_attrs",
    "remaining_attrs",
    "required_any_attrs",
    "required_attrs",
    "unique_attrs",
}
_UNSUPPORTED_TOP_LEVEL_KEYS = {"domain"}
_UNSUPPORTED_WORKFLOW_GROUP_KEYS = {"slot"}
_PSEUDO_GROUP_BODY_KEYS = {"prompt", "fields"}
_PSEUDO_FIELD_KEYS = {"path"}
_CUSTOM_STEP_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_TEMPLATE_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
_CUSTOM_WORKFLOW_RESERVED_NAMES = {
    "workflow",
    "steps",
    "custom_steps",
    "customSteps",
    "template",
    "runtime",
    "output_routes",
    "outputRoutes",
    "leaf_fields",
    "leafFields",
    "field_counts",
    "fieldCounts",
    "schema_hash",
    "schemaHash",
    "metadata_version",
    "metadataVersion",
    "workflow_group",
    "workflowGroup",
    "workflow_field",
    "workflowField",
    "CUSTOM_WORKFLOW_GROUP",
    "CUSTOM_WORKFLOW_FIELD",
    "CUSTOM_WORKFLOW_FINAL_PATH",
    "CUSTOM_WORKFLOW_STEP_NAME",
    "CUSTOM_WORKFLOW_OUTPUT_KEY",
    "CUSTOM_WORKFLOW_READBACK_PATH",
    "final_path",
    "finalPath",
    "step_name",
    "stepName",
    "output_key",
    "outputKey",
    "readback_path",
    "readbackPath",
    "_defs",
    "_pseudo_groups",
    _PERSISTED_WORKFLOW_EXTRACT_KEY,
    "chunk_instruct",
    "chunk_keys",
    "chunk_summary",
    "doc_instruct",
    "doc_keys",
    "doc_summary",
    "document_instruct",
    "document_keys",
    "document_summary",
    "search_query",
    "section_instruct",
    "section_keys",
    "section_summary",
    "sect_instruct",
    "sect_keys",
    "sect_summary",
    "chunk-instruct",
    "chunk-keys",
    "chunk-summary",
    "doc-instruct",
    "doc-keys",
    "doc-summary",
    "search-query",
    "sect-instruct",
    "sect-keys",
    "sect-summary",
}
_CUSTOM_WORKFLOW_AUTHORING_KEYS = {
    "template",
    "custom_steps",
    _CUSTOM_WORKFLOW_AGENT_CHAIN_KEY,
}
_CUSTOM_WORKFLOW_PERSISTED_KEYS = {
    "metadata_version",
    "template",
    "custom_steps",
    _CUSTOM_WORKFLOW_AGENT_CHAIN_KEY,
    "output_routes",
    "leaf_fields",
    "field_counts",
    "schema_hash",
}


def _metadata_factory() -> typing.Dict[str, typing.Any]:
    return {}


def _nested_metadata_factory() -> typing.Dict[str, typing.Dict[str, typing.Any]]:
    return {}


@dataclasses.dataclass(frozen=True)
class FinalFieldPath:
    pointer: str
    segments: typing.Tuple[str, str]

    @classmethod
    def parse(cls, pointer: str) -> "FinalFieldPath":
        if not pointer.startswith("/"):
            raise ValueError(f"invalid final field path [{pointer}]")

        raw_segments = pointer.split("/")[1:]
        if len(raw_segments) != 2 or any(segment == "" for segment in raw_segments):
            raise ValueError(f"unsupported final field path [{pointer}]")

        decoded = tuple(
            _decode_pointer_segment(segment, pointer) for segment in raw_segments
        )
        segments = typing.cast(typing.Tuple[str, str], decoded)
        return cls(pointer=_encode_pointer(segments), segments=segments)

    def to_pointer(self) -> str:
        return _encode_pointer(self.segments)

    def __str__(self) -> str:
        return self.to_pointer()


@dataclasses.dataclass
class PreparedExtractionYaml:
    groups: typing.Dict[str, typing.Dict[str, typing.Any]]
    workflow_groups: typing.Dict[str, typing.Dict[str, typing.Any]]
    pseudo_groups: typing.Dict[str, typing.Dict[str, typing.Any]]
    workflow_field_paths: typing.Dict[str, typing.Dict[str, str]]
    persisted_workflow_extract: typing.Dict[str, typing.Any] = dataclasses.field(
        default_factory=_metadata_factory
    )
    top_level_metadata: typing.Dict[str, typing.Any] = dataclasses.field(
        default_factory=_metadata_factory
    )
    final_group_metadata: typing.Dict[
        str, typing.Dict[str, typing.Any]
    ] = dataclasses.field(default_factory=_nested_metadata_factory)
    workflow_group_metadata: typing.Dict[
        str, typing.Dict[str, typing.Any]
    ] = dataclasses.field(default_factory=_nested_metadata_factory)


def _decode_pointer_segment(segment: str, pointer: str) -> str:
    chars: typing.List[str] = []
    idx = 0
    while idx < len(segment):
        char = segment[idx]
        if char != "~":
            chars.append(char)
            idx += 1
            continue

        if idx + 1 >= len(segment) or segment[idx + 1] not in {"0", "1"}:
            raise ValueError(f"malformed JSON Pointer escape in [{pointer}]")

        chars.append("~" if segment[idx + 1] == "0" else "/")
        idx += 2

    return "".join(chars)


def _encode_pointer(segments: typing.Iterable[str]) -> str:
    encoded: typing.List[str] = []
    for segment in segments:
        encoded.append(segment.replace("~", "~0").replace("/", "~1"))

    return "/" + "/".join(encoded)


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: typing.Any,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> typing.Dict[typing.Any, typing.Any]:
    mapping: typing.Dict[typing.Any, typing.Any] = {}
    for key_node, value_node in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge" or key_node.value == "<<":
            raise ValueError("YAML merge keys are not supported")
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key [{key}]")
        value = loader.construct_object(value_node, deep=deep)
        mapping[key] = value

    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _load_yaml_mapping(raw_yaml: str) -> typing.Dict[str, typing.Any]:
    try:
        data = yaml.load(raw_yaml, Loader=_UniqueKeyLoader)
    except yaml.constructor.ConstructorError as exc:
        if "recursive" in str(exc):
            raise ValueError("cyclic YAML graph detected") from exc
        raise
    if not isinstance(data, dict):
        raise TypeError(f"Expected top-level YAML mapping, got {type(data)}")

    _assert_no_cycles(data, "$", set())
    return typing.cast(typing.Dict[str, typing.Any], data)


def _load_extraction_mapping(raw_yaml: typing.Any) -> typing.Dict[str, typing.Any]:
    if isinstance(raw_yaml, str):
        return _load_yaml_mapping(raw_yaml)

    if not isinstance(raw_yaml, collections.abc.Mapping):
        raise TypeError(f"Expected YAML text or mapping, got {type(raw_yaml)}")

    source_mapping = typing.cast(typing.Mapping[str, typing.Any], raw_yaml)
    raw_mapping = dict(source_mapping)
    _assert_no_cycles(raw_mapping, "$", set())
    return copy.deepcopy(raw_mapping)


def _assert_no_cycles(
    value: typing.Any,
    path: str,
    stack: typing.Set[int],
) -> None:
    if not isinstance(value, (dict, list, tuple)):
        return

    obj_id = id(typing.cast(object, value))
    if obj_id in stack:
        raise ValueError(f"cyclic YAML graph detected at [{path}]")

    stack.add(obj_id)
    if isinstance(value, dict):
        mapping = typing.cast(typing.Dict[typing.Any, typing.Any], value)
        for key, item in mapping.items():
            _assert_no_cycles(item, f"{path}.{key}", stack)
    else:
        sequence = typing.cast(typing.Sequence[typing.Any], value)
        for idx, item in enumerate(sequence):
            _assert_no_cycles(item, f"{path}[{idx}]", stack)
    stack.remove(obj_id)


def _ensure_mapping(value: typing.Any, path: str) -> typing.Dict[str, typing.Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping at [{path}], got {type(value)}")

    return typing.cast(typing.Dict[str, typing.Any], value)


def _raise_unsupported_top_level_metadata(key: str) -> typing.NoReturn:
    raise ValueError(
        f"unsupported top-level metadata [{key}]; generic SDK top-level keys "
        "must be extraction groups with mapping values, reserved SDK keys, or "
        "supported SDK metadata keys. Convert it to supported workflow "
        "metadata before using the generic extraction workflow helpers."
    )


def _reject_unsupported_authored_keys(data: typing.Dict[str, typing.Any]) -> None:
    for key in _UNSUPPORTED_TOP_LEVEL_KEYS:
        if key in data:
            raise ValueError(
                f"top-level [{key}] is not supported in extraction YAML; "
                "use extraction_policy_version: v1 with workflow metadata, or "
                "pure legacy statement/meters/charges YAML"
            )


def _reject_unsupported_workflow_group_keys(
    mapping: typing.Dict[str, typing.Any],
    path: str,
) -> None:
    for key in _UNSUPPORTED_WORKFLOW_GROUP_KEYS:
        if key in mapping:
            raise ValueError(
                f"[{key}] is not supported at [{path}]; use group-level "
                f"[{_CUSTOM_WORKFLOW_GROUP_METADATA_KEY}] in "
                "extraction_policy_version: v1 YAML"
            )


def _validate_policy_version(
    data: typing.Dict[str, typing.Any],
    has_new_yaml_features: bool,
    *,
    has_persisted_workflow_metadata: bool = False,
) -> None:
    has_version = _EXTRACTION_POLICY_VERSION_KEY in data
    if has_persisted_workflow_metadata:
        if has_version and data.get(_EXTRACTION_POLICY_VERSION_KEY) != "v1":
            raise ValueError("extraction_policy_version must be v1")
        return

    if has_new_yaml_features:
        if data.get(_EXTRACTION_POLICY_VERSION_KEY) != "v1":
            raise ValueError(
                "new extraction workflow YAML must set "
                "extraction_policy_version: v1"
            )
        return

    if has_version:
        raise ValueError(
            "pure legacy extraction YAML must not declare "
            "extraction_policy_version"
        )


def _has_supported_policy_metadata(data: typing.Dict[str, typing.Any]) -> bool:
    for key, value in data.items():
        if key in _RESERVED_TOP_LEVEL_KEYS or key in _SUPPORTED_TOP_LEVEL_METADATA_KEYS:
            continue
        if isinstance(value, dict) and set(value) & _SUPPORTED_FINAL_GROUP_METADATA_KEYS:
            return True
    return False


def _has_persisted_workflow_metadata(data: typing.Dict[str, typing.Any]) -> bool:
    workflow = data.get(_CUSTOM_WORKFLOW_KEY)
    return isinstance(workflow, dict) and "metadata_version" in workflow


def _ensure_fields_mapping(
    value: typing.Any, path: str
) -> typing.Dict[str, typing.Any]:
    if value is None:
        return {}

    if not isinstance(value, dict):
        raise ValueError(f"Expected fields mapping at [{path}], got {type(value)}")

    return typing.cast(typing.Dict[str, typing.Any], value)


def _copy_mapping(value: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    return copy.deepcopy(value)


def _strip_custom_workflow_authoring_keys(value: typing.Any) -> None:
    if isinstance(value, dict):
        value.pop(_CUSTOM_WORKFLOW_GROUP_METADATA_KEY, None)
        value.pop(_CUSTOM_WORKFLOW_FIELD_METADATA_KEY, None)
        for key, child in value.items():
            if key == "prompt":
                continue
            _strip_custom_workflow_authoring_keys(child)
    elif isinstance(value, list):
        for child in value:
            _strip_custom_workflow_authoring_keys(child)


def _runtime_safe_authored_extract(
    authored_data: typing.Dict[str, typing.Any],
    custom_workflow_metadata: typing.Optional[typing.Dict[str, typing.Any]],
) -> typing.Dict[str, typing.Any]:
    safe_authored_data = _copy_mapping(authored_data)
    if not custom_workflow_metadata:
        return safe_authored_data

    safe_authored_data[_CUSTOM_WORKFLOW_KEY] = _copy_mapping(custom_workflow_metadata)
    for key, value in safe_authored_data.items():
        if key == _CUSTOM_WORKFLOW_KEY:
            continue
        _strip_custom_workflow_authoring_keys(value)

    return safe_authored_data


def _validate_prompt_shape(mapping: typing.Dict[str, typing.Any], path: str) -> None:
    if "prompt" not in mapping or mapping["prompt"] is None:
        return

    if not isinstance(mapping["prompt"], dict):
        raise ValueError(f"Expected mapping-shaped prompt at [{path}.prompt]")


def _is_group_mapping(value: typing.Any) -> bool:
    if not isinstance(value, dict):
        return False

    mapping = typing.cast(typing.Dict[str, typing.Any], value)
    return isinstance(mapping.get("fields"), dict)


def _is_field_mapping(value: typing.Any) -> bool:
    return isinstance(value, dict) and any(
        key in value for key in ("prompt", "value")
    )


def _validate_prompt_shapes_in_fields(
    fields: typing.Dict[str, typing.Any], path: str
) -> None:
    for field_name, field_value in fields.items():
        field_path = f"{path}.{field_name}"
        if isinstance(field_value, list):
            field_items = typing.cast(typing.List[typing.Any], field_value)
            for idx, item in enumerate(field_items):
                item_path = f"{field_path}[{idx}]"
                item_mapping = _ensure_mapping(item, item_path)
                _validate_prompt_shape(item_mapping, item_path)
                if "fields" in item_mapping:
                    _validate_prompt_shapes_in_fields(
                        _ensure_fields_mapping(
                            item_mapping.get("fields"), f"{item_path}.fields"
                        ),
                        item_path,
                    )
        elif isinstance(field_value, dict):
            field_mapping = typing.cast(typing.Dict[str, typing.Any], field_value)
            _validate_prompt_shape(field_mapping, field_path)
            if "fields" in field_mapping:
                _validate_prompt_shapes_in_fields(
                    _ensure_fields_mapping(
                        field_mapping.get("fields"), f"{field_path}.fields"
                    ),
                    field_path,
                )
            elif not _is_field_mapping(field_mapping):
                _validate_prompt_shapes_in_fields(field_mapping, field_path)
        else:
            raise ValueError(
                f"Unexpected YAML node type for field [{field_path}]: {type(field_value)}"
            )


def _validate_group_shape(group: typing.Dict[str, typing.Any], path: str) -> None:
    _validate_prompt_shape(group, path)
    _validate_prompt_shapes_in_fields(
        _ensure_fields_mapping(group.get("fields"), f"{path}.fields"),
        path,
    )


def _normalize_include(value: typing.Any, path: str) -> typing.List[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, list):
        items = typing.cast(typing.List[typing.Any], value)
        if all(isinstance(item, str) for item in items):
            return typing.cast(typing.List[str], items)

    raise ValueError(f"Expected string or string list at [{path}]")


def _merge_fields(
    target: typing.Dict[str, typing.Any],
    incoming: typing.Dict[str, typing.Any],
    path: str,
) -> None:
    for field_name, field_value in incoming.items():
        if field_name in target:
            raise ValueError(f"duplicate final field name [{path}.{field_name}]")
        target[field_name] = copy.deepcopy(field_value)


def _compose_def_fields(
    defs: typing.Dict[str, typing.Any],
    name: str,
    stack: typing.Tuple[str, ...],
) -> typing.Dict[str, typing.Any]:
    if name not in defs:
        raise ValueError(f"unknown _defs include [{name}]")

    if name in stack:
        cycle = " -> ".join([*stack, name])
        raise ValueError(f"cyclic _defs include [{cycle}]")

    fragment = _ensure_mapping(defs[name], f"_defs.{name}")
    unsupported = set(fragment.keys()) - {"include", "fields"}
    if unsupported:
        raise ValueError(
            f"unsupported _defs keys at [_defs.{name}]: {sorted(unsupported)}"
        )

    fields: typing.Dict[str, typing.Any] = {}
    for include_name in _normalize_include(fragment.get("include"), f"_defs.{name}.include"):
        _merge_fields(
            fields,
            _compose_def_fields(defs, include_name, (*stack, name)),
            f"_defs.{name}",
        )

    _merge_fields(
        fields,
        _ensure_fields_mapping(fragment.get("fields"), f"_defs.{name}.fields"),
        f"_defs.{name}",
    )

    return fields


def _compose_group_fields(
    group_name: str,
    group: typing.Dict[str, typing.Any],
    defs: typing.Dict[str, typing.Any],
) -> typing.Dict[str, typing.Any]:
    group = _copy_mapping(group)
    fields: typing.Dict[str, typing.Any] = {}

    for include_name in _normalize_include(group.pop("include", None), f"{group_name}.include"):
        _merge_fields(
            fields,
            _compose_def_fields(defs, include_name, ()),
            group_name,
        )

    _merge_fields(
        fields,
        _ensure_fields_mapping(group.get("fields"), f"{group_name}.fields"),
        group_name,
    )
    group["fields"] = fields

    return group


def _split_metadata(
    data: typing.Dict[str, typing.Any],
    metadata_keys: typing.Set[str],
) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Dict[str, typing.Any]]:
    body = _copy_mapping(data)
    metadata: typing.Dict[str, typing.Any] = {}
    for key in metadata_keys:
        if key in body:
            metadata[key] = body.pop(key)

    return body, metadata


def _field_for_workflow(
    field: typing.Dict[str, typing.Any], workflow_field_name: str
) -> typing.Dict[str, typing.Any]:
    field = _copy_mapping(field)
    prompt = field.get("prompt")
    if isinstance(prompt, dict):
        prompt["attr_name"] = workflow_field_name

    return field


def _group_prompt_for_workflow(
    group: typing.Dict[str, typing.Any], workflow_group_name: str
) -> typing.Optional[typing.Dict[str, typing.Any]]:
    prompt = group.get("prompt")
    if not isinstance(prompt, dict):
        return None

    prompt = _copy_mapping(typing.cast(typing.Dict[str, typing.Any], prompt))
    prompt["attr_name"] = workflow_group_name
    return prompt


def _resolve_final_field(
    groups: typing.Dict[str, typing.Dict[str, typing.Any]],
    final_path: FinalFieldPath,
) -> typing.Tuple[
    typing.Tuple[str],
    typing.Dict[str, typing.Any],
    str,
    typing.Dict[str, typing.Any],
]:
    root, field_name = final_path.segments
    if root not in groups:
        raise ValueError(f"unknown final field path [{final_path}]")

    parent_group = groups[root]
    fields = _ensure_fields_mapping(parent_group.get("fields"), f"{root}.fields")
    if field_name not in fields:
        raise ValueError(f"unknown final field path [{final_path}]")

    node = fields[field_name]
    if not isinstance(node, dict):
        raise ValueError(f"unknown final field path [{final_path}]")

    node_mapping = typing.cast(typing.Dict[str, typing.Any], node)
    if _is_group_mapping(node_mapping) and not _is_field_mapping(node_mapping):
        raise ValueError(f"final field path points to a group [{final_path}]")

    return (root,), parent_group, field_name, node_mapping


def _remove_final_field_path(
    groups: typing.Dict[str, typing.Dict[str, typing.Any]],
    final_path: FinalFieldPath,
) -> None:
    root, field_name = final_path.segments
    if root not in groups:
        return

    fields = _ensure_fields_mapping(groups[root].get("fields"), f"{root}.fields")
    fields.pop(field_name, None)


def _prune_empty_groups(group: typing.Dict[str, typing.Any]) -> bool:
    raw_fields = group.get("fields")
    if not isinstance(raw_fields, dict):
        return False

    fields = typing.cast(typing.Dict[str, typing.Any], raw_fields)
    for field_name, field_value in list(fields.items()):
        if isinstance(field_value, dict) and _is_group_mapping(field_value):
            if _prune_empty_groups(typing.cast(typing.Dict[str, typing.Any], field_value)):
                fields.pop(field_name)

    return len(fields) == 0


def _collect_field_paths(
    group: typing.Dict[str, typing.Any],
    final_group_name: str,
    prefix: typing.Tuple[str, ...] = (),
) -> typing.Dict[str, str]:
    routes: typing.Dict[str, str] = {}
    fields = _ensure_fields_mapping(group.get("fields"), f"{final_group_name}.fields")
    for field_name, field_value in fields.items():
        workflow_key = ".".join([*prefix, field_name])
        final_path = _encode_pointer((final_group_name, *prefix, field_name))
        if isinstance(field_value, dict):
            field_mapping = typing.cast(typing.Dict[str, typing.Any], field_value)
            if _is_group_mapping(field_mapping) and not _is_field_mapping(field_mapping):
                routes.update(
                    _collect_field_paths(
                        field_mapping,
                        final_group_name,
                        (*prefix, field_name),
                    )
                )
            elif not _is_field_mapping(field_mapping):
                for inner_name in field_mapping:
                    routes[
                        ".".join([*prefix, field_name, inner_name])
                    ] = _encode_pointer((final_group_name, *prefix, field_name, inner_name))
            else:
                routes[workflow_key] = final_path
        else:
            routes[workflow_key] = final_path

    return routes


def _build_identity_route_map(
    groups: typing.Dict[str, typing.Dict[str, typing.Any]]
) -> typing.Dict[str, typing.Dict[str, str]]:
    return {
        group_name: _collect_field_paths(group, group_name)
        for group_name, group in groups.items()
    }


def _without_unset_metadata(
    metadata: typing.Dict[str, typing.Any],
) -> typing.Dict[str, typing.Any]:
    return {key: value for key, value in metadata.items() if value is not None}


def _normalize_template_key(raw: typing.Any, path: str) -> str:
    if not isinstance(raw, str):
        raise ValueError(f"Expected string template key at [{path}]")

    key = raw.strip()
    validation_key = key
    if key.startswith("{{") and key.endswith("}}"):
        validation_key = key[2:-2].strip()

    if not _TEMPLATE_KEY_RE.match(validation_key):
        raise ValueError(f"invalid template key [{raw}]")
    if validation_key.startswith("GROUNDX_"):
        raise ValueError(f"reserved template key prefix [{raw}]")
    if validation_key in _CUSTOM_WORKFLOW_RESERVED_NAMES:
        raise ValueError(f"reserved template key [{raw}]")

    return key


def _normalize_workflow_template(value: typing.Any) -> typing.Dict[str, str]:
    if value is None:
        return {}

    template = _ensure_mapping(value, f"{_CUSTOM_WORKFLOW_KEY}.template")
    normalized: typing.Dict[str, str] = {}
    for raw_key, raw_value in template.items():
        key = _normalize_template_key(
            raw_key, f"{_CUSTOM_WORKFLOW_KEY}.template.{raw_key}"
        )
        if key in normalized:
            raise ValueError(f"duplicate template key [{key}] after normalization")
        if not isinstance(raw_value, str):
            raise ValueError(
                f"Expected string template value at [{_CUSTOM_WORKFLOW_KEY}.template.{raw_key}]"
            )
        normalized[key] = raw_value

    return normalized


def _normalize_agent_chain(
    value: typing.Any,
    workflow_groups: typing.Optional[typing.Set[str]] = None,
) -> typing.Optional[typing.Any]:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{_CUSTOM_WORKFLOW_KEY}.agent_chain must be a list")
    if not value:
        raise ValueError(f"{_CUSTOM_WORKFLOW_KEY}.agent_chain must be a non-empty list")

    _validate_agent_chain(value, workflow_groups or set())
    return copy.deepcopy(value)


def _validate_agent_chain(
    raw_chain: typing.List[typing.Any],
    workflow_groups: typing.Set[str],
) -> None:
    first_stage = raw_chain[0]
    if not isinstance(first_stage, dict) or set(first_stage.keys()) != {"parallel"}:
        raise ValueError(
            f"{_CUSTOM_WORKFLOW_KEY}.agent_chain must start with a parallel stage"
        )

    has_save = False
    serial_start_index = 1
    covered_groups: typing.Set[str] = set()
    for stage_index, raw_stage in enumerate(raw_chain):
        if isinstance(raw_stage, str):
            _validate_agent_chain_task(
                raw_stage,
                f"{_CUSTOM_WORKFLOW_KEY}.agent_chain[{stage_index}]",
            )
            if raw_stage in _CUSTOM_WORKFLOW_AGENT_CHAIN_SAVE_TASKS:
                has_save = True
            continue

        if not isinstance(raw_stage, dict) or set(raw_stage.keys()) != {"parallel"}:
            raise ValueError(
                f"{_CUSTOM_WORKFLOW_KEY}.agent_chain stages must be task strings or "
                "{parallel: [...]}"
            )
        if stage_index != 0:
            raise ValueError(
                "workflow.agent_chain parallel stages after the first stage are not supported"
            )

        raw_branches = raw_stage["parallel"]
        if not isinstance(raw_branches, list) or not raw_branches:
            raise ValueError(
                f"{_CUSTOM_WORKFLOW_KEY}.agent_chain parallel stage must have branches"
            )

        branch_terminal_saves: typing.List[bool] = []
        branch_suffixes: typing.List[str] = []

        for branch_index, raw_branch in enumerate(raw_branches):
            path = (
                f"{_CUSTOM_WORKFLOW_KEY}.agent_chain"
                f"[{stage_index}].parallel[{branch_index}]"
            )
            if not isinstance(raw_branch, dict):
                raise ValueError(f"{path} must be a mapping")
            if set(raw_branch.keys()) != {"group", "chain"}:
                raise ValueError(f"{path} must contain only group and chain")

            group = raw_branch["group"]
            if not isinstance(group, str) or not group:
                raise ValueError(f"{path}.group must be a non-empty string")
            if group not in workflow_groups:
                raise ValueError(f"{path}.group [{group}] is not a workflow group")
            covered_groups.add(group)

            chain = raw_branch["chain"]
            if not isinstance(chain, list) or not chain:
                raise ValueError(f"{path}.chain must be a non-empty list")
            parsed_chain = [
                _validate_agent_chain_task(task, f"{path}.chain")
                for task in chain
            ]
            if any(
                task in _CUSTOM_WORKFLOW_AGENT_CHAIN_SAVE_TASKS
                for task in parsed_chain[:-1]
            ):
                raise ValueError(f"{path}.chain save task must be last")
            suffixes = {_agent_chain_task_suffix(task) for task in parsed_chain}
            if len(suffixes) != 1:
                raise ValueError(f"{path}.chain must use one processing suffix")
            branch_suffixes.append(suffixes.pop())
            branch_terminal_saves.append(
                parsed_chain[-1] in _CUSTOM_WORKFLOW_AGENT_CHAIN_SAVE_TASKS
            )

        terminal_save = _agent_chain_following_save_task(raw_chain, stage_index)
        if any(branch_terminal_saves):
            has_save = True
            serial_start_index = stage_index + 1
            if terminal_save is not None:
                raise ValueError(
                    "workflow.agent_chain parallel branch save tasks cannot be "
                    "combined with a following top-level save task"
                )
            if not all(branch_terminal_saves):
                raise ValueError(
                    "workflow.agent_chain parallel branches must either all end in "
                    "save tasks or all use the following top-level save task"
                )
        elif terminal_save is None:
            raise ValueError(
                "workflow.agent_chain parallel branches must end in a save task or "
                "be followed by one top-level save task"
            )
        else:
            serial_start_index = stage_index + 2
            terminal_suffix = _agent_chain_task_suffix(terminal_save)
            for suffix in branch_suffixes:
                if suffix != terminal_suffix:
                    raise ValueError(
                        "workflow.agent_chain parallel branch processing suffix "
                        "must match following save task"
                    )

    if not has_save:
        raise ValueError(f"{_CUSTOM_WORKFLOW_KEY}.agent_chain must include a save task")
    _validate_agent_chain_serial_tasks(raw_chain, serial_start_index)
    _validate_agent_chain_group_coverage(
        raw_chain,
        workflow_groups,
        covered_groups,
        serial_start_index,
    )


def _validate_agent_chain_serial_tasks(
    raw_chain: typing.List[typing.Any],
    start_index: int,
) -> None:
    stage_index = start_index
    while stage_index < len(raw_chain):
        path = f"{_CUSTOM_WORKFLOW_KEY}.agent_chain[{stage_index}]"
        task = _validate_agent_chain_task(raw_chain[stage_index], path)
        if task in _CUSTOM_WORKFLOW_AGENT_CHAIN_SAVE_TASKS:
            raise ValueError(
                f"{path} top-level save task [{task}] must follow a matching "
                "top-level agent task"
            )

        expected_save = f"save_{_agent_chain_task_suffix(task)}"
        next_index = stage_index + 1
        if next_index >= len(raw_chain):
            raise ValueError(
                f"{path} top-level agent task [{task}] must be followed by "
                f"matching save task [{expected_save}]"
            )

        next_path = f"{_CUSTOM_WORKFLOW_KEY}.agent_chain[{next_index}]"
        next_task = _validate_agent_chain_task(raw_chain[next_index], next_path)
        if next_task != expected_save:
            raise ValueError(
                f"{path} top-level agent task [{task}] must be followed by "
                f"matching save task [{expected_save}]"
            )
        stage_index += 2


def _validate_agent_chain_group_coverage(
    raw_chain: typing.List[typing.Any],
    workflow_groups: typing.Set[str],
    branch_covered_groups: typing.Set[str],
    serial_start_index: int,
) -> None:
    covered_groups = set(branch_covered_groups)
    stage_index = serial_start_index
    while stage_index < len(raw_chain):
        raw_stage = raw_chain[stage_index]
        if (
            isinstance(raw_stage, str)
            and raw_stage in _CUSTOM_WORKFLOW_AGENT_CHAIN_AGENT_TASKS
        ):
            suffix = _agent_chain_task_suffix(raw_stage)
            if suffix in workflow_groups:
                covered_groups.add(suffix)
            stage_index += 2
            continue
        stage_index += 1

    missing_groups = sorted(workflow_groups - covered_groups)
    if missing_groups:
        raise ValueError(
            f"{_CUSTOM_WORKFLOW_KEY}.agent_chain does not cover workflow groups "
            f"[{', '.join(missing_groups)}]"
        )


def _validate_agent_chain_task(task: typing.Any, path: str) -> str:
    if not isinstance(task, str) or not task:
        raise ValueError(f"{path} task must be a non-empty string")
    if task not in _CUSTOM_WORKFLOW_AGENT_CHAIN_SUPPORTED_TASKS:
        raise ValueError(f"{path} contains unsupported task [{task}]")
    return task


def _agent_chain_following_save_task(
    raw_chain: typing.List[typing.Any],
    stage_index: int,
) -> typing.Optional[str]:
    next_index = stage_index + 1
    if next_index >= len(raw_chain):
        return None
    raw_next = raw_chain[next_index]
    if (
        isinstance(raw_next, str)
        and raw_next in _CUSTOM_WORKFLOW_AGENT_CHAIN_SAVE_TASKS
    ):
        return raw_next
    return None


def _agent_chain_task_suffix(task: str) -> str:
    return task.rsplit("_", 1)[-1]


def _valid_custom_workflow_kind(level: str, kind: str) -> bool:
    if level in {"chunk", "section"}:
        return kind in {"instruct", "keys", "summary"}
    if level == "document":
        return kind in {"keys", "summary"}
    return False


def _normalize_required_template_keys(
    value: typing.Any, template: typing.Dict[str, str], path: str
) -> typing.List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"Expected list at [{path}]")

    keys: typing.List[str] = []
    seen: typing.Set[str] = set()
    raw_keys = typing.cast(typing.List[typing.Any], value)
    for idx, raw_key in enumerate(raw_keys):
        key = _normalize_template_key(raw_key, f"{path}[{idx}]")
        if key in seen:
            raise ValueError(f"duplicate required template key [{key}]")
        if key not in template:
            raise ValueError(f"missing template key [{key}]")
        seen.add(key)
        keys.append(key)

    return keys


def _normalize_custom_step_config(
    value: typing.Any, path: str
) -> typing.Optional[typing.Dict[str, typing.Any]]:
    if value is None:
        return None

    config = _ensure_mapping(value, path)
    normalized = _copy_mapping(config)
    for element_name, raw_element_config in normalized.items():
        if raw_element_config is None:
            continue
        element_config = _ensure_mapping(
            raw_element_config, f"{path}.{element_name}"
        )
        if "field" in element_config:
            raise ValueError("custom workflow step config cannot set fixed field")

    return normalized


def _normalize_custom_workflow_steps(
    value: typing.Any,
    template: typing.Dict[str, str],
) -> typing.Tuple[
    typing.List[typing.Dict[str, typing.Any]],
    typing.Dict[str, typing.Dict[str, typing.Any]],
]:
    if value is None:
        return [], {}
    if not isinstance(value, list):
        raise ValueError(f"Expected list at [{_CUSTOM_WORKFLOW_KEY}.custom_steps]")

    steps: typing.List[typing.Dict[str, typing.Any]] = []
    by_name: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    raw_steps = typing.cast(typing.List[typing.Any], value)
    for idx, raw_step in enumerate(raw_steps):
        path = f"{_CUSTOM_WORKFLOW_KEY}.custom_steps[{idx}]"
        step = _ensure_mapping(raw_step, path)
        name = step.get("name")
        if not isinstance(name, str) or not _CUSTOM_STEP_NAME_RE.match(name):
            raise ValueError(f"invalid custom step name [{name}]")
        if name in _CUSTOM_WORKFLOW_RESERVED_NAMES:
            raise ValueError(f"reserved custom step name [{name}]")
        if name in by_name:
            raise ValueError(f"duplicate custom step name [{name}]")

        level = step.get("level")
        kind = step.get("kind")
        if not isinstance(level, str) or not isinstance(kind, str):
            raise ValueError(f"custom step [{name}] is missing level or kind")
        if not _valid_custom_workflow_kind(level, kind):
            raise ValueError(f"invalid custom step level/kind [{level}/{kind}]")

        normalized_step: typing.Dict[str, typing.Any] = {
            "name": name,
            "level": level,
            "kind": kind,
        }
        config = _normalize_custom_step_config(step.get("config"), f"{path}.config")
        if config is not None:
            normalized_step["config"] = config
        required_template_keys = _normalize_required_template_keys(
            step.get("required_template_keys", step.get("requiredTemplateKeys")),
            template,
            f"{path}.required_template_keys",
        )
        if required_template_keys:
            normalized_step["required_template_keys"] = required_template_keys

        steps.append(normalized_step)
        by_name[name] = normalized_step

    return steps, by_name


def _parse_pointer_segments(pointer: typing.Any, path: str) -> typing.Tuple[str, ...]:
    if not isinstance(pointer, str):
        raise ValueError(f"Expected JSON Pointer string at [{path}]")
    if not pointer.startswith("/"):
        raise ValueError(f"finalPath [{pointer}] is not an RFC 6901 JSON Pointer")

    raw_segments = pointer.split("/")[1:]
    if not raw_segments or any(segment == "" for segment in raw_segments):
        raise ValueError(f"unsupported final field path [{pointer}]")

    return tuple(_decode_pointer_segment(segment, pointer) for segment in raw_segments)


def _custom_workflow_output_map(level: str) -> str:
    output_map = _CUSTOM_WORKFLOW_OUTPUT_MAPS.get(level)
    if not output_map:
        raise ValueError(f"invalid custom workflow level [{level}]")
    return output_map


def _custom_workflow_readback_path(
    level: str, step_name: str, output_key: str
) -> str:
    output_map = _custom_workflow_output_map(level)
    if level == "document":
        return f"/{output_map}/{step_name}/{output_key}"

    return f"/chunks/*/{output_map}/{step_name}/{output_key}"


def _validate_output_key(value: typing.Any, path: str) -> str:
    if not isinstance(value, str) or not _CUSTOM_STEP_NAME_RE.match(value):
        raise ValueError(f"invalid output key [{value}] at [{path}]")
    if value in _CUSTOM_WORKFLOW_RESERVED_NAMES:
        raise ValueError(f"reserved output key [{value}] at [{path}]")
    return value


def _field_type(field: typing.Dict[str, typing.Any]) -> str:
    prompt = field.get("prompt")
    if isinstance(prompt, dict):
        prompt_mapping = typing.cast(typing.Dict[str, typing.Any], prompt)
        if isinstance(prompt_mapping.get("type"), str):
            return typing.cast(str, prompt_mapping["type"])

    return "unknown"


def _repetition_scope(segments: typing.Tuple[str, ...]) -> str:
    if "*" not in segments:
        return "none"

    idx = segments.index("*")
    return _encode_pointer(segments[: idx + 1])


def _custom_workflow_field_name(
    prefix: typing.Tuple[str, ...], field_name: str
) -> str:
    return ".".join(segment for segment in (*prefix, field_name) if segment != "*")


def _custom_route_identity(route: typing.Dict[str, typing.Any]) -> str:
    return "\x00".join(
        [
            route["final_path"],
            route["workflow_group"],
            route["workflow_field"],
            route["step_name"],
            route["output_key"],
        ]
    )


def _custom_leaf_identity(leaf: typing.Dict[str, typing.Any]) -> str:
    return "\x00".join(
        [
            leaf["final_path"],
            leaf["workflow_group"],
            leaf["workflow_field"],
            leaf["step_name"],
            leaf["output_key"],
        ]
    )


def _custom_route_leaf_match_key(item: typing.Dict[str, typing.Any]) -> str:
    return "\x00".join(
        [
            item["final_path"],
            item["workflow_group"],
            item["workflow_field"],
            item["step_name"],
            item["level"],
            item["output_key"],
        ]
    )


def _custom_workflow_schema_hash(
    metadata: typing.Dict[str, typing.Any]
) -> str:
    steps: typing.List[typing.Dict[str, typing.Any]] = []
    for step in metadata.get("custom_steps", []):
        normalized_step = {
            "name": step["name"],
            "level": step["level"],
            "kind": step["kind"],
        }
        keys = sorted(step.get("required_template_keys", []))
        if keys:
            normalized_step["required_template_keys"] = keys
        steps.append(normalized_step)

    routes = [
        {
            "final_path": route["final_path"],
            "workflow_group": route["workflow_group"],
            "workflow_field": route["workflow_field"],
            "step_name": route["step_name"],
            "level": route["level"],
            "output_map": route["output_map"],
            "output_key": route["output_key"],
            "readback_path": route["readback_path"],
        }
        for route in metadata.get("output_routes", [])
    ]
    leaves = [
        {
            "final_path": leaf["final_path"],
            "workflow_group": leaf["workflow_group"],
            "workflow_field": leaf["workflow_field"],
            "step_name": leaf["step_name"],
            "level": leaf["level"],
            "output_key": leaf["output_key"],
            "field_type": leaf["field_type"],
            "is_repeated": leaf["is_repeated"],
            "repetition_scope": leaf["repetition_scope"],
        }
        for leaf in metadata.get("leaf_fields", [])
    ]

    steps.sort(key=lambda step: step["name"])
    routes.sort(key=_custom_route_identity)
    leaves.sort(key=_custom_leaf_identity)

    payload: typing.Dict[str, typing.Any] = {
        "metadata_version": metadata.get(
            "metadata_version", _CUSTOM_WORKFLOW_METADATA_VERSION
        )
    }
    if steps:
        payload["custom_steps"] = steps
    if routes:
        payload["output_routes"] = routes
    if leaves:
        payload["leaf_fields"] = leaves

    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_custom_route(
    value: typing.Any,
    idx: int,
    steps_by_name: typing.Dict[str, typing.Dict[str, typing.Any]],
) -> typing.Dict[str, typing.Any]:
    path = f"{_CUSTOM_WORKFLOW_KEY}.output_routes[{idx}]"
    route = _ensure_mapping(value, path)
    normalized: typing.Dict[str, typing.Any] = {}
    for key in (
        "workflow_group",
        "workflow_field",
        "final_path",
        "step_name",
        "level",
        "output_map",
        "output_key",
        "readback_path",
    ):
        raw_value = route.get(key)
        if not isinstance(raw_value, str) or raw_value == "":
            raise ValueError(f"custom workflow output route is missing [{key}]")
        normalized[key] = raw_value

    _parse_pointer_segments(normalized["final_path"], f"{path}.final_path")
    _validate_output_key(normalized["output_key"], f"{path}.output_key")
    step = steps_by_name.get(normalized["step_name"])
    if step is None:
        raise ValueError(f"unknown custom step [{normalized['step_name']}]")
    if normalized["level"] != step["level"]:
        raise ValueError(
            f"route level [{normalized['level']}] does not match step [{step['name']}]"
        )
    if normalized["output_map"] != _custom_workflow_output_map(normalized["level"]):
        raise ValueError(
            f"output map [{normalized['output_map']}] does not match level [{normalized['level']}]"
        )

    return normalized


def _normalize_custom_leaf(
    value: typing.Any,
    idx: int,
    steps_by_name: typing.Dict[str, typing.Dict[str, typing.Any]],
) -> typing.Dict[str, typing.Any]:
    path = f"{_CUSTOM_WORKFLOW_KEY}.leaf_fields[{idx}]"
    leaf = _ensure_mapping(value, path)
    normalized: typing.Dict[str, typing.Any] = {}
    for key in (
        "final_path",
        "workflow_group",
        "workflow_field",
        "step_name",
        "level",
        "output_key",
        "field_type",
        "repetition_scope",
    ):
        raw_value = leaf.get(key)
        if not isinstance(raw_value, str) or raw_value == "":
            raise ValueError(f"custom workflow leaf field is missing [{key}]")
        normalized[key] = raw_value

    is_repeated = leaf.get("is_repeated")
    if not isinstance(is_repeated, bool):
        raise ValueError("custom workflow leaf field is missing [is_repeated]")
    normalized["is_repeated"] = is_repeated

    segments = _parse_pointer_segments(normalized["final_path"], f"{path}.final_path")
    _validate_output_key(normalized["output_key"], f"{path}.output_key")
    step = steps_by_name.get(normalized["step_name"])
    if step is None:
        raise ValueError(f"unknown custom step [{normalized['step_name']}]")
    if normalized["level"] != step["level"]:
        raise ValueError(
            f"leaf level [{normalized['level']}] does not match step [{step['name']}]"
        )
    if normalized["is_repeated"] and "*" not in segments:
        raise ValueError("repeated leaf field must use a literal * path segment")
    if not normalized["is_repeated"] and normalized["repetition_scope"] != "none":
        raise ValueError("non-repeated leaf field cannot set repetition_scope")

    return normalized


def _validate_custom_workflow_routes_and_leaves(
    routes: typing.List[typing.Dict[str, typing.Any]],
    leaves: typing.List[typing.Dict[str, typing.Any]],
) -> typing.Dict[str, int]:
    route_by_match_key: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    leaf_by_match_key: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    route_destinations: typing.Set[typing.Tuple[str, str]] = set()
    counts: typing.Dict[str, int] = {}

    for route in routes:
        match_key = _custom_route_leaf_match_key(route)
        if match_key in route_by_match_key:
            raise ValueError(f"duplicate route identity for [{route['final_path']}]")
        destination = (route["step_name"], route["output_key"])
        if destination in route_destinations:
            raise ValueError(
                "duplicate output destination "
                f"[{route['step_name']}.{route['output_key']}]"
            )
        route_destinations.add(destination)
        route_by_match_key[match_key] = route
        counts[route["step_name"]] = counts.get(route["step_name"], 0) + 1

    for leaf in leaves:
        match_key = _custom_route_leaf_match_key(leaf)
        if match_key in leaf_by_match_key:
            raise ValueError(f"duplicate leaf identity for [{leaf['final_path']}]")
        leaf_by_match_key[match_key] = leaf

    for match_key, route in route_by_match_key.items():
        if match_key not in leaf_by_match_key:
            raise ValueError(f"missing leaf field for route [{route['final_path']}]")
    for match_key, leaf in leaf_by_match_key.items():
        if match_key not in route_by_match_key:
            raise ValueError(f"missing route for leaf field [{leaf['final_path']}]")

    for step_name, count in counts.items():
        if count > _CUSTOM_WORKFLOW_MAX_FIELDS:
            raise ValueError(
                f"custom step [{step_name}] owns {count} fields; "
                f"one executable workflow step may own at most {_CUSTOM_WORKFLOW_MAX_FIELDS} fields"
            )

    return dict(sorted(counts.items()))


def _is_custom_workflow_authoring_metadata(
    workflow: typing.Dict[str, typing.Any]
) -> bool:
    return any(key in workflow for key in _CUSTOM_WORKFLOW_AUTHORING_KEYS)


def _is_custom_workflow_persisted_metadata(
    workflow: typing.Dict[str, typing.Any]
) -> bool:
    return any(key in workflow for key in _CUSTOM_WORKFLOW_PERSISTED_KEYS - _CUSTOM_WORKFLOW_AUTHORING_KEYS)


def _custom_workflow_input(
    data: typing.Dict[str, typing.Any]
) -> typing.Optional[typing.Tuple[str, typing.Dict[str, typing.Any]]]:
    if _CUSTOM_WORKFLOW_KEY not in data:
        return None

    workflow = _ensure_mapping(data[_CUSTOM_WORKFLOW_KEY], _CUSTOM_WORKFLOW_KEY)
    unsupported = set(workflow.keys()) - (
        _CUSTOM_WORKFLOW_AUTHORING_KEYS | _CUSTOM_WORKFLOW_PERSISTED_KEYS
    )
    if unsupported or "fields" in workflow:
        raise ValueError(
            "top-level [workflow] is reserved for custom workflow metadata; "
            "rename the final output group"
        )

    is_persisted = _is_custom_workflow_persisted_metadata(workflow)
    is_authoring = _is_custom_workflow_authoring_metadata(workflow)
    if is_persisted:
        return "persisted", workflow
    if is_authoring:
        return "authoring", workflow

    raise ValueError(
        "top-level [workflow] is reserved for custom workflow metadata; "
        "rename the final output group"
    )


def _normalize_persisted_custom_workflow_metadata(
    workflow: typing.Dict[str, typing.Any]
) -> typing.Dict[str, typing.Any]:
    version = workflow.get("metadata_version")
    if version != _CUSTOM_WORKFLOW_METADATA_VERSION:
        raise ValueError("unsupported custom workflow metadata_version")

    template = _normalize_workflow_template(workflow.get("template"))
    custom_steps, steps_by_name = _normalize_custom_workflow_steps(
        workflow.get("custom_steps"), template
    )
    routes = [
        _normalize_custom_route(route, idx, steps_by_name)
        for idx, route in enumerate(workflow.get("output_routes") or [])
    ]
    leaves = [
        _normalize_custom_leaf(leaf, idx, steps_by_name)
        for idx, leaf in enumerate(workflow.get("leaf_fields") or [])
    ]
    if custom_steps and (not routes or not leaves):
        raise ValueError(
            "custom workflow steps require output routes and leaf fields; "
            "add workflow_output_key metadata to routed fields"
        )
    field_counts = _validate_custom_workflow_routes_and_leaves(routes, leaves)

    caller_field_counts = workflow.get("field_counts")
    if caller_field_counts is not None and caller_field_counts != field_counts:
        raise ValueError("caller field_counts do not match route metadata")

    metadata: typing.Dict[str, typing.Any] = {
        "metadata_version": _CUSTOM_WORKFLOW_METADATA_VERSION,
        "custom_steps": custom_steps,
        "output_routes": routes,
        "leaf_fields": leaves,
    }
    if template:
        metadata["template"] = template
    if field_counts:
        metadata["field_counts"] = field_counts
    agent_chain = _normalize_agent_chain(
        workflow.get(_CUSTOM_WORKFLOW_AGENT_CHAIN_KEY),
        {route["workflow_group"] for route in routes},
    )
    if agent_chain is not None:
        metadata[_CUSTOM_WORKFLOW_AGENT_CHAIN_KEY] = agent_chain

    schema_hash = _custom_workflow_schema_hash(metadata)
    caller_schema_hash = workflow.get("schema_hash")
    if caller_schema_hash is not None and caller_schema_hash != schema_hash:
        raise ValueError("caller schema_hash does not match route metadata")
    metadata["schema_hash"] = schema_hash

    return metadata


def _collect_custom_workflow_routes(
    fields: typing.Dict[str, typing.Any],
    group_name: str,
    step_name: typing.Optional[str],
    steps_by_name: typing.Dict[str, typing.Dict[str, typing.Any]],
    prefix: typing.Tuple[str, ...] = (),
) -> typing.Tuple[
    typing.List[typing.Dict[str, typing.Any]],
    typing.List[typing.Dict[str, typing.Any]],
]:
    routes: typing.List[typing.Dict[str, typing.Any]] = []
    leaves: typing.List[typing.Dict[str, typing.Any]] = []

    for field_name, field_value in fields.items():
        field_path = ".".join([group_name, *prefix, field_name])
        if isinstance(field_value, list):
            field_items = typing.cast(typing.List[typing.Any], field_value)
            for item in field_items:
                item_mapping = _ensure_mapping(item, field_path)
                if _CUSTOM_WORKFLOW_GROUP_METADATA_KEY in item_mapping:
                    raise ValueError(
                        f"field-level workflow_step is not supported at [{field_path}]"
                    )
                if "fields" in item_mapping:
                    item_fields = _ensure_fields_mapping(
                        item_mapping.get("fields"), f"{field_path}.fields"
                    )
                    nested_routes, nested_leaves = _collect_custom_workflow_routes(
                        item_fields,
                        group_name,
                        step_name,
                        steps_by_name,
                        (*prefix, field_name, "*"),
                    )
                    routes.extend(nested_routes)
                    leaves.extend(nested_leaves)
            continue

        if not isinstance(field_value, dict):
            continue

        field_mapping = typing.cast(typing.Dict[str, typing.Any], field_value)
        if _CUSTOM_WORKFLOW_GROUP_METADATA_KEY in field_mapping:
            raise ValueError(
                f"field-level workflow_step is not supported at [{field_path}]"
            )
        output_key_raw = field_mapping.pop(_CUSTOM_WORKFLOW_FIELD_METADATA_KEY, None)
        if output_key_raw is not None:
            if not step_name:
                raise ValueError(
                    f"field [{field_path}] declares workflow_output_key without workflow_step"
                )
            if not isinstance(step_name, str):
                raise ValueError(f"workflow_step for [{field_path}] must be a string")
            step = steps_by_name.get(step_name)
            if step is None:
                raise ValueError(f"unknown custom step [{step_name}]")
            output_key = _validate_output_key(
                output_key_raw,
                f"{field_path}.{_CUSTOM_WORKFLOW_FIELD_METADATA_KEY}",
            )
            segments = (group_name, *prefix, field_name)
            final_path = _encode_pointer(segments)
            level = typing.cast(str, step["level"])
            workflow_field = _custom_workflow_field_name(prefix, field_name)
            route = {
                "workflow_group": group_name,
                "workflow_field": workflow_field,
                "final_path": final_path,
                "step_name": step_name,
                "level": level,
                "output_map": _custom_workflow_output_map(level),
                "output_key": output_key,
                "readback_path": _custom_workflow_readback_path(
                    level, step_name, output_key
                ),
            }
            leaf = {
                "final_path": final_path,
                "workflow_group": group_name,
                "workflow_field": workflow_field,
                "step_name": step_name,
                "level": level,
                "output_key": output_key,
                "field_type": _field_type(field_mapping),
                "is_repeated": "*" in segments,
                "repetition_scope": _repetition_scope(segments),
            }
            routes.append(route)
            leaves.append(leaf)

        if _is_group_mapping(field_mapping) and not _is_field_mapping(field_mapping):
            nested_fields = _ensure_fields_mapping(
                field_mapping.get("fields"), f"{field_path}.fields"
            )
            nested_routes, nested_leaves = _collect_custom_workflow_routes(
                nested_fields,
                group_name,
                step_name,
                steps_by_name,
                (*prefix, field_name),
            )
            routes.extend(nested_routes)
            leaves.extend(nested_leaves)
        elif not _is_field_mapping(field_mapping):
            nested_routes, nested_leaves = _collect_custom_workflow_routes(
                field_mapping,
                group_name,
                step_name,
                steps_by_name,
                (*prefix, field_name),
            )
            routes.extend(nested_routes)
            leaves.extend(nested_leaves)

    return routes, leaves


def _collect_pseudo_custom_workflow_routes(
    group_name: str,
    group: typing.Dict[str, typing.Any],
    step_name: typing.Optional[str],
    steps_by_name: typing.Dict[str, typing.Dict[str, typing.Any]],
    workflow_field_paths: typing.Dict[str, str],
) -> typing.Tuple[
    typing.List[typing.Dict[str, typing.Any]],
    typing.List[typing.Dict[str, typing.Any]],
]:
    if not step_name:
        return [], []
    if not isinstance(step_name, str):
        raise ValueError(f"workflow_step for pseudo group [{group_name}] must be a string")
    step = steps_by_name.get(step_name)
    if step is None:
        raise ValueError(f"unknown custom step [{step_name}]")

    routes: typing.List[typing.Dict[str, typing.Any]] = []
    leaves: typing.List[typing.Dict[str, typing.Any]] = []
    fields = _ensure_fields_mapping(group.get("fields"), f"{group_name}.fields")
    for workflow_field, field_value in fields.items():
        field_path = f"{group_name}.{workflow_field}"
        if not isinstance(field_value, dict):
            continue
        field_mapping = typing.cast(typing.Dict[str, typing.Any], field_value)
        if _CUSTOM_WORKFLOW_GROUP_METADATA_KEY in field_mapping:
            raise ValueError(
                f"field-level workflow_step is not supported at [{field_path}]"
            )
        if _CUSTOM_WORKFLOW_FIELD_METADATA_KEY in field_mapping:
            raise ValueError(
                f"pseudo-routed field [{field_path}] cannot declare "
                f"{_CUSTOM_WORKFLOW_FIELD_METADATA_KEY}; use the pseudo field key"
            )
        output_key = _validate_output_key(workflow_field, field_path)
        final_path = workflow_field_paths.get(workflow_field)
        if final_path is None:
            raise ValueError(
                f"pseudo group [{group_name}] has no final path for [{workflow_field}]"
            )
        level = typing.cast(str, step["level"])
        route = {
            "workflow_group": group_name,
            "workflow_field": workflow_field,
            "final_path": final_path,
            "step_name": step_name,
            "level": level,
            "output_map": _custom_workflow_output_map(level),
            "output_key": output_key,
            "readback_path": _custom_workflow_readback_path(
                level, step_name, output_key
            ),
        }
        leaf = {
            "final_path": final_path,
            "workflow_group": group_name,
            "workflow_field": workflow_field,
            "step_name": step_name,
            "level": level,
            "output_key": output_key,
            "field_type": _field_type(field_mapping),
            "is_repeated": "*" in _parse_pointer_segments(final_path, field_path),
            "repetition_scope": _repetition_scope(
                _parse_pointer_segments(final_path, field_path)
            ),
        }
        routes.append(route)
        leaves.append(leaf)

    return routes, leaves


def _build_authored_custom_workflow_metadata(
    workflow: typing.Dict[str, typing.Any],
    workflow_groups: typing.Dict[str, typing.Dict[str, typing.Any]],
    workflow_group_metadata: typing.Dict[str, typing.Dict[str, typing.Any]],
    workflow_field_paths: typing.Dict[str, typing.Dict[str, str]],
    pseudo_group_names: typing.Set[str],
) -> typing.Dict[str, typing.Any]:
    template = _normalize_workflow_template(workflow.get("template"))
    custom_steps, steps_by_name = _normalize_custom_workflow_steps(
        workflow.get("custom_steps"), template
    )
    if not custom_steps:
        raise ValueError("workflow.custom_steps is required for custom workflow metadata")

    routes: typing.List[typing.Dict[str, typing.Any]] = []
    leaves: typing.List[typing.Dict[str, typing.Any]] = []
    for group_name, group in workflow_groups.items():
        group_step = workflow_group_metadata.get(group_name, {}).get(
            _CUSTOM_WORKFLOW_GROUP_METADATA_KEY
        )
        if group_step and group_step not in steps_by_name:
            raise ValueError(f"unknown custom step [{group_step}]")
        fields = _ensure_fields_mapping(group.get("fields"), f"{group_name}.fields")
        if group_name in pseudo_group_names:
            group_routes, group_leaves = _collect_pseudo_custom_workflow_routes(
                group_name,
                group,
                typing.cast(typing.Optional[str], group_step),
                steps_by_name,
                workflow_field_paths.get(group_name, {}),
            )
        else:
            group_routes, group_leaves = _collect_custom_workflow_routes(
                fields,
                group_name,
                typing.cast(typing.Optional[str], group_step),
                steps_by_name,
            )
        routes.extend(group_routes)
        leaves.extend(group_leaves)

    if not routes or not leaves:
        raise ValueError(
            "custom workflow steps require output routes and leaf fields; "
            "add workflow_output_key metadata to routed fields"
        )
    field_counts = _validate_custom_workflow_routes_and_leaves(routes, leaves)
    metadata: typing.Dict[str, typing.Any] = {
        "metadata_version": _CUSTOM_WORKFLOW_METADATA_VERSION,
        "custom_steps": custom_steps,
        "output_routes": routes,
        "leaf_fields": leaves,
    }
    if template:
        metadata["template"] = template
    if field_counts:
        metadata["field_counts"] = field_counts
    agent_chain = _normalize_agent_chain(
        workflow.get(_CUSTOM_WORKFLOW_AGENT_CHAIN_KEY),
        {route["workflow_group"] for route in routes},
    )
    if agent_chain is not None:
        metadata[_CUSTOM_WORKFLOW_AGENT_CHAIN_KEY] = agent_chain
    metadata["schema_hash"] = _custom_workflow_schema_hash(metadata)
    return metadata


def _apply_custom_workflow_field_paths(
    workflow_field_paths: typing.Dict[str, typing.Dict[str, str]],
    custom_workflow_metadata: typing.Optional[typing.Dict[str, typing.Any]],
) -> None:
    if not custom_workflow_metadata:
        return

    for route in custom_workflow_metadata.get("output_routes", []):
        group_name = route["workflow_group"]
        workflow_field = route["workflow_field"]
        final_path = route["final_path"]
        workflow_field_paths.setdefault(group_name, {})[workflow_field] = final_path


def _has_declared_metadata(
    data: typing.Dict[str, typing.Any],
    top_metadata_keys: typing.Set[str],
    final_metadata_keys: typing.Set[str],
    workflow_metadata_keys: typing.Set[str],
) -> bool:
    if "_defs" in data or "_pseudo_groups" in data or _CUSTOM_WORKFLOW_KEY in data:
        return True

    if any(key in data for key in top_metadata_keys):
        return True

    group_metadata_keys = final_metadata_keys | workflow_metadata_keys
    for group_name, group_data in data.items():
        if group_name in _RESERVED_TOP_LEVEL_KEYS or group_name in top_metadata_keys:
            continue
        if isinstance(group_data, dict) and any(
            key in group_data for key in group_metadata_keys
        ):
            return True

    return False


def _persisted_workflow_extract(
    authored_data: typing.Dict[str, typing.Any],
    workflow_groups: typing.Dict[str, typing.Dict[str, typing.Any]],
    top_metadata_keys: typing.Set[str],
    final_metadata_keys: typing.Set[str],
    workflow_metadata_keys: typing.Set[str],
    custom_workflow_metadata: typing.Optional[typing.Dict[str, typing.Any]] = None,
) -> typing.Dict[str, typing.Any]:
    persisted: typing.Dict[str, typing.Any] = _copy_mapping(workflow_groups)
    if custom_workflow_metadata:
        persisted[_CUSTOM_WORKFLOW_KEY] = _copy_mapping(custom_workflow_metadata)
    if _has_declared_metadata(
        authored_data,
        top_metadata_keys,
        final_metadata_keys,
        workflow_metadata_keys,
    ):
        persisted[_PERSISTED_WORKFLOW_EXTRACT_KEY] = _runtime_safe_authored_extract(
            authored_data,
            custom_workflow_metadata,
        )

    return persisted


def _resolve_pseudo_workflow_metadata(
    pseudo_group_name: str,
    explicit_metadata: typing.Dict[str, typing.Any],
    parent_paths: typing.Set[typing.Tuple[str, ...]],
    final_workflow_metadata: typing.Dict[str, typing.Dict[str, typing.Any]],
    workflow_metadata_keys: typing.Set[str],
) -> typing.Dict[str, typing.Any]:
    resolved: typing.Dict[str, typing.Any] = {}

    for key in workflow_metadata_keys:
        explicit_value = explicit_metadata.get(key)
        if explicit_value is not None:
            resolved[key] = explicit_value
            continue

        parent_values: typing.List[typing.Any] = []
        missing_parent_count = 0
        for parent_path in sorted(parent_paths):
            parent_name = parent_path[0]
            parent_metadata = final_workflow_metadata.get(parent_name, {})
            parent_value = parent_metadata.get(key)
            if parent_value is None:
                missing_parent_count += 1
            else:
                parent_values.append(parent_value)

        if not parent_values:
            continue

        if missing_parent_count:
            raise ValueError(
                f"pseudo group [_pseudo_groups.{pseudo_group_name}] has ambiguous "
                f"workflow metadata [{key}]; explicit [{key}] is required"
            )

        first_value = parent_values[0]
        if any(value != first_value for value in parent_values[1:]):
            raise ValueError(
                f"pseudo group [_pseudo_groups.{pseudo_group_name}] has ambiguous "
                f"workflow metadata [{key}]; explicit [{key}] is required"
            )

        resolved[key] = first_value

    return resolved


def prepare_extraction_yaml(
    raw_yaml: typing.Union[str, typing.Mapping[str, typing.Any]],
    top_level_metadata_keys: typing.Optional[typing.Iterable[str]] = None,
    final_group_metadata_keys: typing.Optional[typing.Iterable[str]] = None,
    workflow_group_metadata_keys: typing.Optional[typing.Iterable[str]] = None,
) -> PreparedExtractionYaml:
    data = _load_extraction_mapping(raw_yaml)
    if _PERSISTED_WORKFLOW_EXTRACT_KEY in data:
        persisted_outer_data = _copy_mapping(data)
        data = _copy_mapping(
            _ensure_mapping(
                data[_PERSISTED_WORKFLOW_EXTRACT_KEY],
                _PERSISTED_WORKFLOW_EXTRACT_KEY,
            )
        )
        persisted_workflow = persisted_outer_data.get(_CUSTOM_WORKFLOW_KEY)
        if isinstance(
            persisted_workflow, dict
        ) and _is_custom_workflow_persisted_metadata(persisted_workflow):
            data[_CUSTOM_WORKFLOW_KEY] = _copy_mapping(persisted_workflow)
    custom_workflow_kind_and_input = _custom_workflow_input(data)
    is_persisted_custom_workflow = (
        custom_workflow_kind_and_input is not None
        and custom_workflow_kind_and_input[0] == "persisted"
    )
    _reject_unsupported_authored_keys(data)
    has_persisted_workflow_metadata = _has_persisted_workflow_metadata(data)
    _validate_policy_version(
        data,
        bool(
            (custom_workflow_kind_and_input and not is_persisted_custom_workflow)
            or "_pseudo_groups" in data
            or _has_supported_policy_metadata(data)
        ),
        has_persisted_workflow_metadata=has_persisted_workflow_metadata,
    )
    top_metadata_key_set = set(_SUPPORTED_TOP_LEVEL_METADATA_KEYS)
    top_metadata_key_set.update(top_level_metadata_keys or [])
    final_metadata_key_set = set(_SUPPORTED_FINAL_GROUP_METADATA_KEYS)
    final_metadata_key_set.update(final_group_metadata_keys or [])
    workflow_metadata_key_set = set(workflow_group_metadata_keys or [])
    effective_workflow_metadata_key_set = workflow_metadata_key_set | {
        _CUSTOM_WORKFLOW_GROUP_METADATA_KEY
    }
    metadata_overlap = final_metadata_key_set & effective_workflow_metadata_key_set
    if metadata_overlap:
        raise ValueError(
            "metadata keys cannot be both final-group and workflow-group scoped: "
            f"{sorted(metadata_overlap)}"
        )

    top_level_metadata: typing.Dict[str, typing.Any] = {}
    for key in top_metadata_key_set:
        if key in data:
            top_level_metadata[key] = data[key]

    defs: typing.Dict[str, typing.Any] = {}
    if "_defs" in data:
        defs = _ensure_mapping(data["_defs"], "_defs")

    raw_groups: typing.Dict[str, typing.Any] = {}
    for group_name, group_data in data.items():
        if group_name in _RESERVED_TOP_LEVEL_KEYS or group_name in top_metadata_key_set:
            continue
        raw_groups[group_name] = group_data

    groups: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    final_group_metadata: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    final_workflow_metadata: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    for group_name, raw_group in raw_groups.items():
        if not isinstance(raw_group, dict):
            _raise_unsupported_top_level_metadata(group_name)
        group = _ensure_mapping(raw_group, group_name)
        _reject_unsupported_workflow_group_keys(group, group_name)
        group, final_metadata = _split_metadata(group, final_metadata_key_set)
        group, workflow_metadata = _split_metadata(
            group, effective_workflow_metadata_key_set
        )
        group = _compose_group_fields(group_name, group, defs)
        _validate_group_shape(group, group_name)
        groups[group_name] = group
        if final_metadata:
            final_group_metadata[group_name] = final_metadata
        workflow_metadata = _without_unset_metadata(workflow_metadata)
        if workflow_metadata:
            final_workflow_metadata[group_name] = workflow_metadata

    custom_workflow_metadata: typing.Optional[typing.Dict[str, typing.Any]] = None
    custom_workflow_authoring_input: typing.Optional[typing.Dict[str, typing.Any]] = None
    if custom_workflow_kind_and_input:
        custom_workflow_kind, custom_workflow_input = custom_workflow_kind_and_input
        if custom_workflow_kind == "persisted":
            custom_workflow_metadata = _normalize_persisted_custom_workflow_metadata(
                custom_workflow_input
            )
        else:
            custom_workflow_authoring_input = custom_workflow_input

    raw_pseudo_groups: typing.Dict[str, typing.Any] = {}
    if "_pseudo_groups" in data:
        raw_pseudo_groups = _ensure_mapping(data["_pseudo_groups"], "_pseudo_groups")

    pseudo_groups: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    workflow_group_metadata: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    workflow_field_paths: typing.Dict[str, typing.Dict[str, str]] = {}
    routed_final_paths: typing.Dict[str, FinalFieldPath] = {}

    for pseudo_group_name, raw_pseudo_group in raw_pseudo_groups.items():
        if pseudo_group_name in groups:
            raise ValueError(
                f"pseudo group [{pseudo_group_name}] collides with a final group"
            )

        pseudo_group = _ensure_mapping(
            raw_pseudo_group, f"_pseudo_groups.{pseudo_group_name}"
        )
        _reject_unsupported_workflow_group_keys(
            pseudo_group,
            f"_pseudo_groups.{pseudo_group_name}",
        )
        pseudo_group, explicit_workflow_metadata = _split_metadata(
            pseudo_group, effective_workflow_metadata_key_set
        )
        unsupported_pseudo_keys = set(pseudo_group.keys()) - _PSEUDO_GROUP_BODY_KEYS
        if unsupported_pseudo_keys:
            raise ValueError(
                f"unsupported pseudo-group keys at [_pseudo_groups.{pseudo_group_name}]: "
                f"{sorted(unsupported_pseudo_keys)}"
            )
        _validate_prompt_shape(pseudo_group, f"_pseudo_groups.{pseudo_group_name}")
        if "fields" not in pseudo_group:
            raise ValueError(
                f"pseudo group [_pseudo_groups.{pseudo_group_name}] is missing fields"
            )

        pseudo_fields = _ensure_fields_mapping(
            pseudo_group.get("fields"), f"_pseudo_groups.{pseudo_group_name}.fields"
        )
        if not pseudo_fields:
            raise ValueError(
                f"pseudo group [_pseudo_groups.{pseudo_group_name}] has empty fields"
            )
        workflow_fields: typing.Dict[str, typing.Any] = {}
        route_map: typing.Dict[str, str] = {}
        parent_paths: typing.Set[typing.Tuple[str, ...]] = set()
        parent_groups: typing.Dict[
            typing.Tuple[str, ...], typing.Dict[str, typing.Any]
        ] = {}

        for workflow_field_name, raw_pseudo_field in pseudo_fields.items():
            _validate_output_key(
                workflow_field_name,
                f"_pseudo_groups.{pseudo_group_name}.fields.{workflow_field_name}",
            )
            pseudo_field = _ensure_mapping(
                raw_pseudo_field,
                f"_pseudo_groups.{pseudo_group_name}.fields.{workflow_field_name}",
            )
            unsupported = set(pseudo_field.keys()) - _PSEUDO_FIELD_KEYS
            if unsupported:
                raise ValueError(
                    "pseudo-group field "
                    f"[_pseudo_groups.{pseudo_group_name}.fields.{workflow_field_name}] "
                    f"declares unsupported keys: {sorted(unsupported)}"
                )
            if "path" not in pseudo_field:
                raise ValueError(
                    "pseudo-group field "
                    f"[_pseudo_groups.{pseudo_group_name}.fields.{workflow_field_name}] "
                    "is missing path"
                )
            final_path = pseudo_field["path"]
            if not isinstance(final_path, str):
                raise ValueError(
                    "pseudo-group field "
                    f"[_pseudo_groups.{pseudo_group_name}.fields.{workflow_field_name}.path] "
                    "must be a string"
                )
            final_field_path = FinalFieldPath.parse(final_path)
            final_pointer = final_field_path.to_pointer()
            if final_pointer in routed_final_paths:
                raise ValueError(f"final field path [{final_pointer}] routed more than once")

            parent_path, parent_group, _field_name, final_field = _resolve_final_field(
                groups,
                final_field_path,
            )
            if _CUSTOM_WORKFLOW_FIELD_METADATA_KEY in final_field:
                raise ValueError(
                    f"pseudo-routed final field [{final_pointer}] cannot declare "
                    f"{_CUSTOM_WORKFLOW_FIELD_METADATA_KEY}; use the pseudo field key"
                )
            routed_final_paths[final_pointer] = final_field_path
            parent_paths.add(parent_path)
            parent_groups[parent_path] = parent_group
            workflow_fields[workflow_field_name] = _field_for_workflow(
                final_field, workflow_field_name
            )
            route_map[workflow_field_name] = final_pointer

        workflow_group = {
            key: copy.deepcopy(value)
            for key, value in pseudo_group.items()
            if key != "fields"
        }
        if "prompt" not in workflow_group and len(parent_paths) == 1:
            inherited_parent_path = next(iter(parent_paths))
            inherited_prompt = _group_prompt_for_workflow(
                parent_groups[inherited_parent_path], pseudo_group_name
            )
            if inherited_prompt:
                workflow_group["prompt"] = inherited_prompt
        elif "prompt" not in workflow_group and len(parent_paths) > 1:
            raise ValueError(
                f"pseudo group [_pseudo_groups.{pseudo_group_name}] spans multiple "
                "final parent groups and must declare prompt"
            )
        workflow_group["fields"] = workflow_fields
        _validate_group_shape(workflow_group, f"_pseudo_groups.{pseudo_group_name}")

        pseudo_groups[pseudo_group_name] = workflow_group
        workflow_field_paths[pseudo_group_name] = route_map
        resolved_metadata = _resolve_pseudo_workflow_metadata(
            pseudo_group_name,
            explicit_workflow_metadata,
            parent_paths,
            final_workflow_metadata,
            effective_workflow_metadata_key_set,
        )
        if resolved_metadata:
            workflow_group_metadata[pseudo_group_name] = resolved_metadata

    if not pseudo_groups:
        workflow_groups = _copy_mapping(groups)
        workflow_field_paths = _build_identity_route_map(groups)
        workflow_group_metadata = _copy_mapping(final_workflow_metadata)
        if custom_workflow_authoring_input is not None:
            custom_workflow_metadata = _build_authored_custom_workflow_metadata(
                custom_workflow_authoring_input,
                workflow_groups,
                workflow_group_metadata,
                workflow_field_paths,
                set(),
            )
            _strip_custom_workflow_authoring_keys(groups)
            _strip_custom_workflow_authoring_keys(workflow_groups)
        _apply_custom_workflow_field_paths(
            workflow_field_paths,
            custom_workflow_metadata,
        )
        return PreparedExtractionYaml(
            groups=groups,
            workflow_groups=workflow_groups,
            pseudo_groups={},
            workflow_field_paths=workflow_field_paths,
            persisted_workflow_extract=_persisted_workflow_extract(
                data,
                workflow_groups,
                top_metadata_key_set,
                final_metadata_key_set,
                effective_workflow_metadata_key_set,
                custom_workflow_metadata,
            ),
            top_level_metadata=top_level_metadata,
            final_group_metadata=final_group_metadata,
            workflow_group_metadata=workflow_group_metadata,
        )

    residual_groups = _copy_mapping(groups)
    for final_path in routed_final_paths.values():
        _remove_final_field_path(residual_groups, final_path)

    for group_name in list(residual_groups.keys()):
        if _prune_empty_groups(residual_groups[group_name]):
            residual_groups.pop(group_name)

    workflow_groups = _copy_mapping(pseudo_groups)
    for group_name, group in residual_groups.items():
        workflow_groups[group_name] = group
        workflow_field_paths[group_name] = _collect_field_paths(group, group_name)
        if group_name in final_workflow_metadata:
            workflow_group_metadata[group_name] = copy.deepcopy(
                final_workflow_metadata[group_name]
            )
    _apply_custom_workflow_field_paths(
        workflow_field_paths,
        custom_workflow_metadata,
    )
    if custom_workflow_authoring_input is not None:
        custom_workflow_metadata = _build_authored_custom_workflow_metadata(
            custom_workflow_authoring_input,
            workflow_groups,
            workflow_group_metadata,
            workflow_field_paths,
            set(pseudo_groups.keys()),
        )
        _strip_custom_workflow_authoring_keys(groups)
        _strip_custom_workflow_authoring_keys(workflow_groups)
        _apply_custom_workflow_field_paths(
            workflow_field_paths,
            custom_workflow_metadata,
        )

    return PreparedExtractionYaml(
        groups=groups,
        workflow_groups=workflow_groups,
        pseudo_groups=_copy_mapping(pseudo_groups),
        workflow_field_paths=workflow_field_paths,
        persisted_workflow_extract=_persisted_workflow_extract(
            data,
            workflow_groups,
            top_metadata_key_set,
            final_metadata_key_set,
            effective_workflow_metadata_key_set,
            custom_workflow_metadata,
        ),
        top_level_metadata=top_level_metadata,
        final_group_metadata=final_group_metadata,
        workflow_group_metadata=workflow_group_metadata,
    )


def element_from_mapping(data: typing.Dict[str, typing.Any]) -> Element:
    if "fields" in data:
        return group_from_mapping(data)

    return ExtractedField(**data)


def group_from_mapping(
    data: typing.Dict[str, typing.Any], key: typing.Optional[str] = None
) -> Group:
    prompt_data = data.get("prompt")
    prompt: typing.Optional[Prompt] = None

    if prompt_data:
        prompt = Prompt(**prompt_data)
        if key and not prompt.attr_name:
            prompt.attr_name = key

    raw_fields: typing.Dict[str, typing.Any] = data.get("fields", {}) or {}
    fields: typing.Dict[
        str,
        typing.Union[
            Element,
            typing.Dict[str, Element],
            typing.Sequence[Element],
        ],
    ] = {}

    for name, n in raw_fields.items():
        if isinstance(n, list):
            nl = typing.cast(typing.List[typing.Any], n)
            elements_list: typing.List[Element] = []
            for item in nl:
                if not isinstance(item, dict):
                    raise TypeError(
                        f"Expected dict for list item under field '{name}', got {type(item)}"
                    )
                res = typing.cast(typing.Dict[str, typing.Any], item)
                if "prompt" in res and "attr_name" not in res["prompt"]:
                    res["prompt"]["attr_name"] = name
                elem = element_from_mapping(res)
                elements_list.append(elem)
            fields[name] = elements_list
        elif isinstance(n, dict):
            nd = typing.cast(typing.Dict[str, typing.Any], n)
            if "prompt" in nd or "fields" in nd or "value" in nd:
                if "prompt" in nd and "attr_name" not in nd["prompt"]:
                    nd["prompt"]["attr_name"] = name
                elem = element_from_mapping(nd)
                fields[name] = elem
            else:
                inner_dict: typing.Dict[str, Element] = {}
                for sub_name, sub_node in nd.items():
                    if not isinstance(sub_node, dict):
                        raise TypeError(
                            f"Expected dict for '{name}.{sub_name}', got {type(sub_node)}"
                        )
                    res = typing.cast(typing.Dict[str, typing.Any], sub_node)
                    if "prompt" in res and "attr_name" not in res["prompt"]:
                        res["prompt"]["attr_name"] = sub_name
                    inner_dict[sub_name] = element_from_mapping(res)
                fields[name] = inner_dict
        else:
            raise TypeError(f"Unexpected YAML node type for field '{name}': {type(n)}")

    return Group(prompt=prompt, fields=fields)


def load_from_mapping(data: typing.Dict[str, typing.Any]) -> typing.Dict[str, Group]:
    grps: typing.Dict[str, Group] = {}
    for k, v in data.items():
        group = _ensure_mapping(v, k)
        grps[k] = group_from_mapping(group, k)

    return grps


def load_from_yaml(raw_yaml: str) -> typing.Dict[str, Group]:
    prepared = prepare_extraction_yaml(raw_yaml)

    return load_from_mapping(prepared.groups)


def do_not_remove_fields(grp: Group) -> Group:
    grp.remove_fields = False
    if grp.prompt and grp.prompt.attr_name:
        grp.prompt.attr_name = None
    for i in grp.fields:
        if isinstance(grp.fields[i], Group):
            ngrp = typing.cast(Group, grp.fields[i])
            grp.fields[i] = do_not_remove_fields(ngrp)
        elif not isinstance(grp.fields[i], list):
            fld = typing.cast(ExtractedField, grp.fields[i])
            if fld.prompt and fld.prompt.attr_name:
                fld.prompt.attr_name = None
            grp.fields[i] = fld

    return grp
