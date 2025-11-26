import typing, yaml

from ..classes.element import Element
from ..classes.field import ExtractedField
from ..classes.group import Group
from ..classes.prompt import Prompt


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


def load_from_yaml(raw_yaml: str) -> typing.Dict[str, Group]:
    data = yaml.safe_load(raw_yaml)
    if not isinstance(data, dict):
        raise TypeError(f"Expected top-level YAML mapping, got {type(data)}")

    grps: typing.Dict[str, Group] = {}
    data = typing.cast(typing.Dict[str, typing.Any], data)
    for k, v in data.items():
        grps[k] = group_from_mapping(v, k)

    return grps


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
