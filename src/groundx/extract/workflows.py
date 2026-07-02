import copy
import dataclasses
import inspect
import typing
from collections.abc import Mapping, Sequence
from pathlib import Path

from .prompt import PreparedExtractionYaml, prepare_extraction_yaml

_PERSISTED_WORKFLOW_EXTRACT_KEY = "_groundx_persisted_extract"
_WORKFLOW_METADATA_KEY = "workflow"
_WORKFLOW_METADATA_VERSION = 1
_WORKFLOW_EXTRACT_MAPPING_KIND = "workflow_extract"
_AUTHORED_YAML_MAPPING_KIND = "authored_yaml"
_AUTHORING_ONLY_WORKFLOW_KEYS = {"workflow_step", "workflow_output_key"}
_PERSISTED_WORKFLOW_METADATA_KEYS = {
    "agent_chain",
    "metadata_version",
    "output_routes",
    "leaf_fields",
    "field_counts",
    "schema_hash",
}
_FIXED_DEFAULT_STEP_KEYS = (
    "chunk-instruct",
    "chunk-keys",
    "chunk-summary",
    "doc-keys",
    "doc-summary",
    "sect-instruct",
    "sect-summary",
)
_UNRELEASED_WORKFLOW_KWARGS = (
    "custom_steps",
    "output_routes",
    "leaf_fields",
)
_CUSTOM_STEP_ALIASES = {
    "requiredTemplateKeys": "required_template_keys",
}
_OUTPUT_ROUTE_ALIASES = {
    "workflowGroup": "workflow_group",
    "workflowField": "workflow_field",
    "finalPath": "final_path",
    "stepName": "step_name",
    "outputMap": "output_map",
    "outputKey": "output_key",
    "readbackPath": "readback_path",
}
_LEAF_FIELD_ALIASES = {
    "finalPath": "final_path",
    "workflowGroup": "workflow_group",
    "workflowField": "workflow_field",
    "stepName": "step_name",
    "outputKey": "output_key",
    "fieldType": "field_type",
    "isRepeated": "is_repeated",
    "repetitionScope": "repetition_scope",
}


@dataclasses.dataclass(frozen=True)
class ExtractionDefinition:
    """
    Loaded extraction workflow settings.
    """

    extract: typing.Dict[str, typing.Any]
    prepared: typing.Optional[PreparedExtractionYaml] = None
    template: typing.Optional[typing.Dict[str, str]] = None
    custom_steps: typing.Optional[typing.Sequence[typing.Any]] = None
    output_routes: typing.Optional[typing.Sequence[typing.Any]] = None
    leaf_fields: typing.Optional[typing.Sequence[typing.Any]] = None
    chunk_strategy: typing.Optional[typing.Any] = None
    section_strategy: typing.Optional[typing.Any] = None
    steps: typing.Optional[typing.Any] = None


def load_extraction_definition_from_yaml(
    *,
    path: typing.Any = ...,
    yaml_text: typing.Any = ...,
    mapping: typing.Any = ...,
    prepared: typing.Any = ...,
    mapping_kind: typing.Optional[str] = None,
) -> ExtractionDefinition:
    source_name, source_value = _select_source(
        path=path,
        yaml_text=yaml_text,
        mapping=mapping,
        prepared=prepared,
    )

    if mapping_kind is not None and source_name != "mapping":
        raise ValueError("mapping_kind is only valid when mapping is the selected source")

    if source_name == "path":
        source_path = Path(source_value)
        raw_yaml = source_path.read_text(encoding="utf-8")
        prepared_value = _prepare_extraction_yaml_with_context(
            raw_yaml,
            f"path [{source_path}]",
        )
        return _definition_from_prepared(prepared_value)

    if source_name == "yaml_text":
        prepared_value = _prepare_extraction_yaml_with_context(
            source_value,
            "yaml_text",
        )
        return _definition_from_prepared(prepared_value)

    if source_name == "prepared":
        if not isinstance(source_value, PreparedExtractionYaml):
            raise TypeError("prepared must be a PreparedExtractionYaml")
        return _definition_from_prepared(source_value)

    if source_name == "mapping":
        effective_kind = mapping_kind or _AUTHORED_YAML_MAPPING_KIND
        if effective_kind not in {_AUTHORED_YAML_MAPPING_KIND, _WORKFLOW_EXTRACT_MAPPING_KIND}:
            raise ValueError(
                "mapping_kind must be 'authored_yaml' or 'workflow_extract'"
            )

        mapping_value = _ensure_mapping(source_value, "mapping")
        if effective_kind == _WORKFLOW_EXTRACT_MAPPING_KIND:
            return _definition_from_workflow_extract(mapping_value)

        if _looks_like_workflow_extract_mapping(mapping_value):
            raise ValueError(
                "mapping looks like an existing workflow extract; pass "
                "mapping_kind='workflow_extract' to load it explicitly"
            )
        prepared_value = _prepare_extraction_yaml_with_context(
            mapping_value,
            "mapping",
        )
        return _definition_from_prepared(prepared_value)

    raise AssertionError(f"unsupported source {source_name}")


def load_extraction_definition_from_workflow_response(
    workflow_id: str,
    response: typing.Any,
) -> ExtractionDefinition:
    workflow = getattr(response, "workflow", None)
    if workflow is None and isinstance(response, Mapping):
        response_mapping = typing.cast(typing.Mapping[str, typing.Any], response)
        workflow = response_mapping.get("workflow")
    if workflow is None:
        raise ValueError(f"workflow [{workflow_id}] response did not include a workflow")

    extract = _get_workflow_value(workflow, "extract")
    if not isinstance(extract, Mapping):
        raise ValueError(f"workflow [{workflow_id}] does not include extraction config")

    extract_mapping = _deepcopy_mapping(
        typing.cast(typing.Mapping[str, typing.Any], extract)
    )
    fallback_metadata = _workflow_metadata(extract_mapping)

    template = _first_present(
        _get_workflow_value(workflow, "template"),
        fallback_metadata.get("template"),
    )
    custom_steps = _first_present(
        _get_workflow_value(workflow, "custom_steps"),
        fallback_metadata.get("custom_steps"),
    )
    output_routes = _first_present(
        _get_workflow_value(workflow, "output_routes"),
        fallback_metadata.get("output_routes"),
    )
    leaf_fields = _first_present(
        _get_workflow_value(workflow, "leaf_fields"),
        fallback_metadata.get("leaf_fields"),
    )

    return ExtractionDefinition(
        extract=extract_mapping,
        prepared=_prepared_from_workflow_extract(extract_mapping),
        template=_normalize_template(template),
        custom_steps=_plain_metadata_sequence(custom_steps, _CUSTOM_STEP_ALIASES),
        output_routes=_plain_metadata_sequence(output_routes, _OUTPUT_ROUTE_ALIASES),
        leaf_fields=_plain_metadata_sequence(leaf_fields, _LEAF_FIELD_ALIASES),
        chunk_strategy=_get_workflow_value(workflow, "chunk_strategy"),
        section_strategy=_get_workflow_value(workflow, "section_strategy"),
        steps=_plain_or_none(_get_workflow_value(workflow, "steps")),
    )


def resolve_extraction_definition_source(
    *,
    definition: typing.Any = ...,
    path: typing.Any = ...,
    yaml_text: typing.Any = ...,
    mapping: typing.Any = ...,
    prepared: typing.Any = ...,
    mapping_kind: typing.Optional[str] = None,
) -> ExtractionDefinition:
    if definition is not ...:
        if mapping_kind is not None:
            raise ValueError("mapping_kind is only valid when mapping is the selected source")
        if not isinstance(definition, ExtractionDefinition):
            raise TypeError("definition must be an ExtractionDefinition")
        return definition

    source_name, _source_value = _select_source(
        path=path,
        yaml_text=yaml_text,
        mapping=mapping,
        prepared=prepared,
    )
    if mapping_kind is not None and source_name != "mapping":
        raise ValueError("mapping_kind is only valid when mapping is the selected source")

    return load_extraction_definition_from_yaml(
        path=path,
        yaml_text=yaml_text,
        mapping=mapping,
        prepared=prepared,
        mapping_kind=mapping_kind,
    )


def workflow_kwargs_from_extraction_definition(
    definition: ExtractionDefinition,
    *,
    name: typing.Any = ...,
    require_name: bool = False,
    chunk_strategy: typing.Any = ...,
    section_strategy: typing.Any = ...,
    steps: typing.Any = ...,
    request_options: typing.Any = None,
) -> typing.Dict[str, typing.Any]:
    if require_name and (name is ... or name is None or name == ""):
        raise ValueError("name is required when creating an extraction workflow")

    kwargs: typing.Dict[str, typing.Any] = {"extract": copy.deepcopy(definition.extract)}
    if name is not ... and name is not None:
        kwargs["name"] = name

    template = _normalize_template(definition.template)
    if template is not None:
        kwargs["template"] = template
    if definition.custom_steps is not None:
        kwargs["custom_steps"] = copy.deepcopy(definition.custom_steps)
    if definition.output_routes is not None:
        kwargs["output_routes"] = copy.deepcopy(definition.output_routes)
    if definition.leaf_fields is not None:
        kwargs["leaf_fields"] = copy.deepcopy(definition.leaf_fields)

    resolved_chunk_strategy = _resolve_defaulted_value(
        supplied=chunk_strategy,
        preserved=definition.chunk_strategy,
        default="element",
    )
    if resolved_chunk_strategy is not None:
        kwargs["chunk_strategy"] = resolved_chunk_strategy

    resolved_section_strategy = _resolve_defaulted_value(
        supplied=section_strategy,
        preserved=definition.section_strategy,
        default=None,
    )
    if resolved_section_strategy is not None:
        kwargs["section_strategy"] = resolved_section_strategy

    resolved_steps = _resolve_defaulted_value(
        supplied=steps,
        preserved=definition.steps,
        default=None,
    )
    if resolved_steps is None and definition.custom_steps:
        resolved_steps = disabled_fixed_default_steps()
    if resolved_steps is not None:
        kwargs["steps"] = resolved_steps

    if request_options is not None:
        kwargs["request_options"] = request_options

    return kwargs


def ensure_workflow_method_supports_kwargs(
    method: typing.Any,
    kwargs: typing.Mapping[str, typing.Any],
) -> None:
    unsupported = [
        key for key in _UNRELEASED_WORKFLOW_KWARGS
        if key in kwargs and not _method_accepts_keyword(method, key)
    ]
    if unsupported:
        unsupported_list = ", ".join(unsupported)
        raise RuntimeError(
            "This GroundX SDK build cannot create or update extraction "
            "workflows with custom workflow steps yet. Regenerate and publish "
            "the SDK from the Fern/OpenAPI schema before using: "
            f"{unsupported_list}."
        )


def disabled_fixed_default_steps() -> typing.Dict[str, None]:
    return {field: None for field in _FIXED_DEFAULT_STEP_KEYS}


def _definition_from_prepared(prepared: PreparedExtractionYaml) -> ExtractionDefinition:
    extract = copy.deepcopy(prepared.persisted_workflow_extract)
    metadata = _workflow_metadata(extract)
    return ExtractionDefinition(
        extract=extract,
        prepared=prepared,
        template=_normalize_template(metadata.get("template")),
        custom_steps=_plain_metadata_sequence(
            metadata.get("custom_steps"),
            _CUSTOM_STEP_ALIASES,
        ),
        output_routes=_plain_metadata_sequence(
            metadata.get("output_routes"),
            _OUTPUT_ROUTE_ALIASES,
        ),
        leaf_fields=_plain_metadata_sequence(
            metadata.get("leaf_fields"),
            _LEAF_FIELD_ALIASES,
        ),
    )


def _definition_from_workflow_extract(
    extract: typing.Mapping[str, typing.Any],
) -> ExtractionDefinition:
    extract_mapping = _deepcopy_mapping(extract)
    prepared = _validate_workflow_extract_mapping(extract_mapping)
    metadata = _workflow_metadata(extract_mapping)
    return ExtractionDefinition(
        extract=extract_mapping,
        prepared=prepared,
        template=_normalize_template(metadata.get("template")),
        custom_steps=_plain_metadata_sequence(
            metadata.get("custom_steps"),
            _CUSTOM_STEP_ALIASES,
        ),
        output_routes=_plain_metadata_sequence(
            metadata.get("output_routes"),
            _OUTPUT_ROUTE_ALIASES,
        ),
        leaf_fields=_plain_metadata_sequence(
            metadata.get("leaf_fields"),
            _LEAF_FIELD_ALIASES,
        ),
    )


def _prepared_from_workflow_extract(
    extract: typing.Mapping[str, typing.Any],
) -> typing.Optional[PreparedExtractionYaml]:
    if _PERSISTED_WORKFLOW_EXTRACT_KEY not in extract:
        return None
    return prepare_extraction_yaml(extract)


def _validate_workflow_extract_mapping(
    extract: typing.Mapping[str, typing.Any],
) -> typing.Optional[PreparedExtractionYaml]:
    authoring_paths = _find_authoring_only_workflow_keys(extract)
    if authoring_paths:
        preview = ", ".join(authoring_paths[:3])
        raise ValueError(
            "workflow_extract contains authoring-only workflow metadata "
            f"at {preview}; load authored YAML without mapping_kind or persist a "
            "workflow extract with workflow.metadata_version"
        )

    metadata = _workflow_metadata(extract)
    has_workflow_metadata = bool(set(metadata.keys()) & _PERSISTED_WORKFLOW_METADATA_KEYS)
    if not has_workflow_metadata:
        return _prepared_from_workflow_extract(extract)

    if metadata.get("metadata_version") != _WORKFLOW_METADATA_VERSION:
        raise ValueError("unsupported custom workflow metadata_version")

    prepared = prepare_extraction_yaml(extract)
    _validate_workflow_metadata_references(extract, metadata)
    if _PERSISTED_WORKFLOW_EXTRACT_KEY in extract:
        return prepared
    return None


def _find_authoring_only_workflow_keys(
    value: typing.Any,
    *,
    path: str = "$",
    parent_key: typing.Optional[str] = None,
) -> typing.List[str]:
    if not isinstance(value, Mapping):
        return []

    paths: typing.List[str] = []
    mapping = typing.cast(typing.Mapping[str, typing.Any], value)
    for key, child in mapping.items():
        if path == "$" and key in {
            _PERSISTED_WORKFLOW_EXTRACT_KEY,
            _WORKFLOW_METADATA_KEY,
        }:
            continue

        child_path = f"{path}.{key}"
        is_name_position = parent_key == "fields"
        if (
            isinstance(key, str)
            and key in _AUTHORING_ONLY_WORKFLOW_KEYS
            and not is_name_position
        ):
            paths.append(child_path)

        paths.extend(
            _find_authoring_only_workflow_keys(
                child,
                path=child_path,
                parent_key=key if isinstance(key, str) else None,
            )
        )

    return paths


def _validate_workflow_metadata_references(
    extract: typing.Mapping[str, typing.Any],
    metadata: typing.Mapping[str, typing.Any],
) -> None:
    for metadata_key in ("output_routes", "leaf_fields"):
        entries = metadata.get(metadata_key)
        if entries is None:
            continue
        if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
            raise ValueError(f"workflow.{metadata_key} must be a list")
        for idx, entry in enumerate(entries):
            if not isinstance(entry, Mapping):
                raise ValueError(f"workflow.{metadata_key}[{idx}] must be a mapping")
            entry_mapping = typing.cast(typing.Mapping[str, typing.Any], entry)
            group_name = entry_mapping.get("workflow_group")
            field_name = entry_mapping.get("workflow_field")
            if not isinstance(group_name, str) or group_name == "":
                raise ValueError(f"workflow.{metadata_key}[{idx}] is missing workflow_group")
            if not isinstance(field_name, str) or field_name == "":
                raise ValueError(f"workflow.{metadata_key}[{idx}] is missing workflow_field")
            if not _workflow_field_exists(extract, group_name, field_name):
                raise ValueError(
                    f"workflow.{metadata_key}[{idx}] references missing "
                    f"workflow field [{group_name}.{field_name}]"
                )


def _workflow_field_exists(
    extract: typing.Mapping[str, typing.Any],
    group_name: str,
    workflow_field: str,
) -> bool:
    group = extract.get(group_name)
    if not isinstance(group, Mapping):
        return False

    fields = group.get("fields")
    if not isinstance(fields, Mapping):
        return False

    current: typing.Any = fields
    parts = workflow_field.split(".")
    for idx, part in enumerate(parts):
        if not isinstance(current, Mapping) or part not in current:
            return False
        value = current[part]
        if idx == len(parts) - 1:
            return True
        if isinstance(value, list):
            if not value:
                return False
            value = value[0]
        if isinstance(value, Mapping) and isinstance(value.get("fields"), Mapping):
            current = value["fields"]
            continue
        if isinstance(value, Mapping):
            current = value
            continue
        return False

    return False


def _prepare_extraction_yaml_with_context(
    source: typing.Union[str, typing.Mapping[str, typing.Any]],
    context: str,
) -> PreparedExtractionYaml:
    try:
        return prepare_extraction_yaml(source)
    except ValueError as exc:
        raise ValueError(f"failed to load extraction YAML from {context}: {exc}") from exc


def _select_source(**sources: typing.Any) -> typing.Tuple[str, typing.Any]:
    selected = [(name, value) for name, value in sources.items() if value is not ...]
    if len(selected) != 1:
        source_names = ", ".join(sources.keys())
        if not selected:
            raise ValueError(f"expected exactly one source: {source_names}")
        conflicts = ", ".join(name for name, _value in selected)
        raise ValueError(
            f"expected exactly one source from {source_names}; received {conflicts}"
        )
    return selected[0]


def _looks_like_workflow_extract_mapping(
    mapping: typing.Mapping[str, typing.Any],
) -> bool:
    workflow = mapping.get(_WORKFLOW_METADATA_KEY)
    if not isinstance(workflow, Mapping):
        return _PERSISTED_WORKFLOW_EXTRACT_KEY in mapping
    workflow_mapping = typing.cast(typing.Mapping[str, typing.Any], workflow)
    return bool(set(workflow_mapping.keys()) & _PERSISTED_WORKFLOW_METADATA_KEYS)


def _workflow_metadata(
    extract: typing.Mapping[str, typing.Any],
) -> typing.Mapping[str, typing.Any]:
    metadata = extract.get(_WORKFLOW_METADATA_KEY)
    if isinstance(metadata, Mapping):
        return typing.cast(typing.Mapping[str, typing.Any], metadata)
    return {}


def _normalize_template(value: typing.Any) -> typing.Optional[typing.Dict[str, str]]:
    if value is None:
        return None
    mapping = _ensure_any_mapping(value, "template")
    template: typing.Dict[str, str] = {}
    for key, template_value in mapping.items():
        if not isinstance(key, str):
            raise ValueError("workflow template keys must be strings")
        if not isinstance(template_value, str):
            raise ValueError(
                f"workflow template value for [{key}] must be a string"
            )
        template[key] = template_value
    return template or None


def _ensure_mapping(
    value: typing.Any,
    name: str,
) -> typing.Mapping[str, typing.Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    return typing.cast(typing.Mapping[str, typing.Any], value)


def _ensure_any_mapping(
    value: typing.Any,
    name: str,
) -> typing.Mapping[typing.Any, typing.Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    return typing.cast(typing.Mapping[typing.Any, typing.Any], value)


def _deepcopy_mapping(
    value: typing.Mapping[str, typing.Any],
) -> typing.Dict[str, typing.Any]:
    return copy.deepcopy(dict(value))


def _plain_sequence(value: typing.Any) -> typing.Optional[typing.Sequence[typing.Any]]:
    if value is None:
        return None
    return typing.cast(typing.Sequence[typing.Any], _plain_or_none(value))


def _plain_metadata_sequence(
    value: typing.Any,
    aliases: typing.Mapping[str, str],
) -> typing.Optional[typing.Sequence[typing.Any]]:
    sequence = _plain_sequence(value)
    if sequence is None:
        return None
    return [_normalize_mapping_aliases(item, aliases) for item in sequence]


def _plain_or_none(value: typing.Any) -> typing.Any:
    if value is None:
        return None
    if isinstance(value, Mapping):
        mapping = typing.cast(typing.Mapping[typing.Any, typing.Any], value)
        return {key: _plain_or_none(item) for key, item in mapping.items()}
    if isinstance(value, (list, tuple)):
        sequence = typing.cast(typing.Sequence[typing.Any], value)
        return [_plain_or_none(item) for item in sequence]
    if hasattr(value, "model_dump"):
        return value.model_dump(
            by_alias=False,
            exclude_none=True,
            exclude_unset=True,
        )
    if hasattr(value, "dict"):
        return value.dict(by_alias=False, exclude_none=True, exclude_unset=True)
    return copy.deepcopy(value)


def _normalize_mapping_aliases(
    value: typing.Any,
    aliases: typing.Mapping[str, str],
) -> typing.Any:
    if isinstance(value, Mapping):
        mapping = typing.cast(typing.Mapping[typing.Any, typing.Any], value)
        return {
            aliases.get(key, key): _normalize_mapping_aliases(item, aliases)
            for key, item in mapping.items()
        }
    if isinstance(value, (list, tuple)):
        sequence = typing.cast(typing.Sequence[typing.Any], value)
        return [_normalize_mapping_aliases(item, aliases) for item in sequence]
    return value


def _get_workflow_value(workflow: typing.Any, name: str) -> typing.Any:
    if isinstance(workflow, Mapping):
        workflow_mapping = typing.cast(typing.Mapping[str, typing.Any], workflow)
        return workflow_mapping.get(name)
    return getattr(workflow, name, None)


def _first_present(*values: typing.Any) -> typing.Any:
    for value in values:
        if value is not None:
            return value
    return None


def _resolve_defaulted_value(
    *,
    supplied: typing.Any,
    preserved: typing.Any,
    default: typing.Any,
) -> typing.Any:
    if supplied is not ...:
        return supplied
    if preserved is not None:
        return preserved
    return default


def _method_accepts_keyword(method: typing.Any, key: str) -> bool:
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return False
    for parameter in signature.parameters.values():
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            return True
        if parameter.kind in {
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        } and parameter.name == key:
            return True
    return False
