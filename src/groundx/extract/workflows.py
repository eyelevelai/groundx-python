import copy
import dataclasses
import typing
from collections.abc import Mapping
from pathlib import Path

from ..types import WorkflowSteps
from .prompt import PreparedExtractionYaml, prepare_extraction_yaml

_PERSISTED_WORKFLOW_EXTRACT_KEY = "_groundx_persisted_extract"
_WORKFLOW_METADATA_KEY = "workflow"
_WORKFLOW_EXTRACT_MAPPING_KIND = "workflow_extract"
_AUTHORED_YAML_MAPPING_KIND = "authored_yaml"
_PERSISTED_WORKFLOW_METADATA_KEYS = {
    "metadata_version",
    "output_routes",
    "leaf_fields",
    "field_counts",
    "schema_hash",
}
_FIXED_DEFAULT_STEP_FIELDS = (
    "chunk_instruct",
    "chunk_keys",
    "chunk_summary",
    "doc_keys",
    "doc_summary",
    "sect_instruct",
    "sect_summary",
)


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
        raw_yaml = Path(source_value).read_text(encoding="utf-8")
        prepared_value = prepare_extraction_yaml(raw_yaml)
        return _definition_from_prepared(prepared_value)

    if source_name == "yaml_text":
        prepared_value = prepare_extraction_yaml(source_value)
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
        prepared_value = prepare_extraction_yaml(mapping_value)
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
        custom_steps=_plain_sequence(custom_steps),
        output_routes=_plain_sequence(output_routes),
        leaf_fields=_plain_sequence(leaf_fields),
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
    source_name, source_value = _select_source(
        definition=definition,
        path=path,
        yaml_text=yaml_text,
        mapping=mapping,
        prepared=prepared,
    )
    if mapping_kind is not None and source_name != "mapping":
        raise ValueError("mapping_kind is only valid when mapping is the selected source")

    if source_name == "definition":
        if not isinstance(source_value, ExtractionDefinition):
            raise TypeError("definition must be an ExtractionDefinition")
        return source_value

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


def disabled_fixed_default_steps() -> WorkflowSteps:
    return WorkflowSteps(
        **{field: None for field in _FIXED_DEFAULT_STEP_FIELDS}
    )


def _definition_from_prepared(prepared: PreparedExtractionYaml) -> ExtractionDefinition:
    extract = copy.deepcopy(prepared.persisted_workflow_extract)
    metadata = _workflow_metadata(extract)
    return ExtractionDefinition(
        extract=extract,
        prepared=prepared,
        template=_normalize_template(metadata.get("template")),
        custom_steps=_plain_sequence(metadata.get("custom_steps")),
        output_routes=_plain_sequence(metadata.get("output_routes")),
        leaf_fields=_plain_sequence(metadata.get("leaf_fields")),
    )


def _definition_from_workflow_extract(
    extract: typing.Mapping[str, typing.Any],
) -> ExtractionDefinition:
    extract_mapping = _deepcopy_mapping(extract)
    metadata = _workflow_metadata(extract_mapping)
    return ExtractionDefinition(
        extract=extract_mapping,
        prepared=_prepared_from_workflow_extract(extract_mapping),
        template=_normalize_template(metadata.get("template")),
        custom_steps=_plain_sequence(metadata.get("custom_steps")),
        output_routes=_plain_sequence(metadata.get("output_routes")),
        leaf_fields=_plain_sequence(metadata.get("leaf_fields")),
    )


def _prepared_from_workflow_extract(
    extract: typing.Mapping[str, typing.Any],
) -> typing.Optional[PreparedExtractionYaml]:
    if _PERSISTED_WORKFLOW_EXTRACT_KEY not in extract:
        return None
    return prepare_extraction_yaml(extract)


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
