import copy
import dataclasses
import typing

import yaml
from ..classes.element import Element
from ..classes.field import ExtractedField
from ..classes.group import Group
from ..classes.prompt import Prompt

_RESERVED_TOP_LEVEL_KEYS = {"_defs", "_pseudo_groups"}
_UNSUPPORTED_PSEUDO_FIELD_KEYS = {"prompt", "fields", "value"}


def _metadata_factory() -> typing.Dict[str, typing.Any]:
    return {}


def _nested_metadata_factory() -> typing.Dict[str, typing.Dict[str, typing.Any]]:
    return {}


@dataclasses.dataclass
class PreparedExtractionYaml:
    groups: typing.Dict[str, typing.Dict[str, typing.Any]]
    workflow_groups: typing.Dict[str, typing.Dict[str, typing.Any]]
    pseudo_groups: typing.Dict[str, typing.Dict[str, typing.Any]]
    workflow_field_paths: typing.Dict[str, typing.Dict[str, str]]
    top_level_metadata: typing.Dict[str, typing.Any] = dataclasses.field(
        default_factory=_metadata_factory
    )
    group_metadata: typing.Dict[str, typing.Dict[str, typing.Any]] = dataclasses.field(
        default_factory=_nested_metadata_factory
    )
    pseudo_group_metadata: typing.Dict[
        str, typing.Dict[str, typing.Any]
    ] = dataclasses.field(default_factory=_nested_metadata_factory)


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: typing.Any,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> typing.Dict[typing.Any, typing.Any]:
    loader.flatten_mapping(node)
    mapping: typing.Dict[typing.Any, typing.Any] = {}
    for key_node, value_node in node.value:
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
    data = yaml.load(raw_yaml, Loader=_UniqueKeyLoader)
    if not isinstance(data, dict):
        raise TypeError(f"Expected top-level YAML mapping, got {type(data)}")

    return typing.cast(typing.Dict[str, typing.Any], data)


def _ensure_mapping(value: typing.Any, path: str) -> typing.Dict[str, typing.Any]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping at [{path}], got {type(value)}")

    return typing.cast(typing.Dict[str, typing.Any], value)


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
    final_path: str,
) -> typing.Tuple[
    typing.Tuple[str, ...],
    typing.Dict[str, typing.Any],
    str,
    typing.Dict[str, typing.Any],
]:
    parts = tuple(part for part in final_path.split(".") if part)
    if len(parts) < 2:
        raise ValueError(f"malformed final field path [{final_path}]")

    root = parts[0]
    if root not in groups:
        raise ValueError(f"unknown final field path [{final_path}]")

    parent_path: typing.List[str] = [root]
    parent_group = groups[root]
    fields = _ensure_fields_mapping(parent_group.get("fields"), f"{root}.fields")

    for idx, part in enumerate(parts[1:], start=1):
        if part not in fields:
            raise ValueError(f"unknown final field path [{final_path}]")

        node = fields[part]
        is_last = idx == len(parts) - 1

        if is_last:
            if not isinstance(node, dict):
                raise ValueError(f"unknown final field path [{final_path}]")
            node_mapping = typing.cast(typing.Dict[str, typing.Any], node)
            if _is_group_mapping(node_mapping) and not _is_field_mapping(node_mapping):
                raise ValueError(f"final field path points to a group [{final_path}]")
            return tuple(parent_path), parent_group, part, node_mapping

        if not isinstance(node, dict):
            raise ValueError(f"unknown final field path [{final_path}]")

        node_mapping = typing.cast(typing.Dict[str, typing.Any], node)
        if _is_group_mapping(node_mapping):
            parent_group = node_mapping
            parent_path.append(part)
            fields = _ensure_fields_mapping(
                parent_group.get("fields"), f"{'.'.join(parent_path)}.fields"
            )
        elif not _is_field_mapping(node_mapping):
            parent_path.append(part)
            fields = node_mapping
        else:
            raise ValueError(f"unknown final field path [{final_path}]")

    raise ValueError(f"unknown final field path [{final_path}]")


def _remove_final_field_path(
    groups: typing.Dict[str, typing.Dict[str, typing.Any]],
    final_path: str,
) -> None:
    parts = tuple(part for part in final_path.split(".") if part)
    if len(parts) < 2 or parts[0] not in groups:
        return

    fields = _ensure_fields_mapping(groups[parts[0]].get("fields"), f"{parts[0]}.fields")
    for part in parts[1:-1]:
        node = fields.get(part)
        if not isinstance(node, dict):
            return
        node_mapping = typing.cast(typing.Dict[str, typing.Any], node)
        if _is_group_mapping(node_mapping):
            fields = _ensure_fields_mapping(
                node_mapping.get("fields"), f"{'.'.join(parts)}.fields"
            )
        elif not _is_field_mapping(node_mapping):
            fields = node_mapping
        else:
            return

    fields.pop(parts[-1], None)


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
        final_path = ".".join([final_group_name, *prefix, field_name])
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
                    ] = ".".join([final_group_name, *prefix, field_name, inner_name])
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


def prepare_extraction_yaml(
    raw_yaml: str,
    top_level_metadata_keys: typing.Optional[typing.Iterable[str]] = None,
    group_metadata_keys: typing.Optional[typing.Iterable[str]] = None,
    pseudo_group_metadata_keys: typing.Optional[typing.Iterable[str]] = None,
) -> PreparedExtractionYaml:
    data = _load_yaml_mapping(raw_yaml)
    top_metadata_key_set = set(top_level_metadata_keys or [])
    group_metadata_key_set = set(group_metadata_keys or [])
    pseudo_metadata_key_set = set(pseudo_group_metadata_keys or group_metadata_key_set)

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
    group_metadata: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    for group_name, raw_group in raw_groups.items():
        group = _ensure_mapping(raw_group, group_name)
        group, metadata = _split_metadata(group, group_metadata_key_set)
        group = _compose_group_fields(group_name, group, defs)
        _validate_group_shape(group, group_name)
        groups[group_name] = group
        if metadata:
            group_metadata[group_name] = metadata

    raw_pseudo_groups: typing.Dict[str, typing.Any] = {}
    if "_pseudo_groups" in data:
        raw_pseudo_groups = _ensure_mapping(data["_pseudo_groups"], "_pseudo_groups")

    pseudo_groups: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    pseudo_group_metadata: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
    workflow_field_paths: typing.Dict[str, typing.Dict[str, str]] = {}
    routed_final_paths: typing.Set[str] = set()

    for pseudo_group_name, raw_pseudo_group in raw_pseudo_groups.items():
        if pseudo_group_name in groups:
            raise ValueError(
                f"pseudo group [{pseudo_group_name}] collides with a final group"
            )

        pseudo_group = _ensure_mapping(
            raw_pseudo_group, f"_pseudo_groups.{pseudo_group_name}"
        )
        pseudo_group, metadata = _split_metadata(
            pseudo_group, pseudo_metadata_key_set
        )
        _validate_prompt_shape(pseudo_group, f"_pseudo_groups.{pseudo_group_name}")
        if "fields" not in pseudo_group:
            raise ValueError(
                f"pseudo group [_pseudo_groups.{pseudo_group_name}] is missing fields"
            )

        pseudo_fields = _ensure_fields_mapping(
            pseudo_group.get("fields"), f"_pseudo_groups.{pseudo_group_name}.fields"
        )
        workflow_fields: typing.Dict[str, typing.Any] = {}
        route_map: typing.Dict[str, str] = {}
        parent_paths: typing.Set[typing.Tuple[str, ...]] = set()
        parent_groups: typing.Dict[
            typing.Tuple[str, ...], typing.Dict[str, typing.Any]
        ] = {}

        for workflow_field_name, raw_pseudo_field in pseudo_fields.items():
            pseudo_field = _ensure_mapping(
                raw_pseudo_field,
                f"_pseudo_groups.{pseudo_group_name}.fields.{workflow_field_name}",
            )
            unsupported = set(pseudo_field.keys()) & _UNSUPPORTED_PSEUDO_FIELD_KEYS
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
            if final_path in routed_final_paths:
                raise ValueError(f"final field path [{final_path}] routed more than once")

            parent_path, parent_group, _field_name, final_field = _resolve_final_field(
                groups,
                final_path,
            )
            routed_final_paths.add(final_path)
            parent_paths.add(parent_path)
            parent_groups[parent_path] = parent_group
            workflow_fields[workflow_field_name] = _field_for_workflow(
                final_field, workflow_field_name
            )
            route_map[workflow_field_name] = final_path

        workflow_group = {
            key: copy.deepcopy(value)
            for key, value in pseudo_group.items()
            if key != "fields"
        }
        if "prompt" not in workflow_group and len(parent_paths) == 1:
            parent_path = next(iter(parent_paths))
            inherited_prompt = _group_prompt_for_workflow(
                parent_groups[parent_path], pseudo_group_name
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
        if metadata:
            pseudo_group_metadata[pseudo_group_name] = metadata

    if not pseudo_groups:
        return PreparedExtractionYaml(
            groups=groups,
            workflow_groups=_copy_mapping(groups),
            pseudo_groups={},
            workflow_field_paths=_build_identity_route_map(groups),
            top_level_metadata=top_level_metadata,
            group_metadata=group_metadata,
            pseudo_group_metadata=pseudo_group_metadata,
        )

    residual_groups = _copy_mapping(groups)
    for final_path in routed_final_paths:
        _remove_final_field_path(residual_groups, final_path)

    for group_name in list(residual_groups.keys()):
        if _prune_empty_groups(residual_groups[group_name]):
            residual_groups.pop(group_name)

    workflow_groups = _copy_mapping(pseudo_groups)
    for group_name, group in residual_groups.items():
        workflow_groups[group_name] = group
        workflow_field_paths[group_name] = _collect_field_paths(group, group_name)

    return PreparedExtractionYaml(
        groups=groups,
        workflow_groups=workflow_groups,
        pseudo_groups=_copy_mapping(pseudo_groups),
        workflow_field_paths=workflow_field_paths,
        top_level_metadata=top_level_metadata,
        group_metadata=group_metadata,
        pseudo_group_metadata=pseudo_group_metadata,
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
