import typing, yaml

from ..classes.element import Element
from ..classes.field import ExtractedField
from ..classes.group import Group
from ..classes.prompt import Prompt


def element_from_mapping(
    data: typing.Dict[str, typing.Any], key: typing.Optional[str] = None
) -> Element:
    if "fields" in data:
        grp = group_from_mapping(data)
        if key and grp.prompt and not grp.prompt.attr_name:
            grp.prompt.attr_name = key
        return grp

    if any(k in data for k in ("value", "conflicts", "confidence")):
        ef = ExtractedField(**data)
        if key and ef.prompt and not ef.prompt.attr_name:
            ef.prompt.attr_name = key
        return ef

    ele = Element(**data)
    if key and ele.prompt and not ele.prompt.attr_name:
        ele.prompt.attr_name = key

    return ele


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
                elem = element_from_mapping(
                    typing.cast(typing.Dict[str, typing.Any], item), name
                )
                elements_list.append(elem)
            fields[name] = elements_list
        elif isinstance(n, dict):
            nd = typing.cast(typing.Dict[str, typing.Any], n)
            if "prompt" in nd or "fields" in nd or "value" in nd:
                elem = element_from_mapping(nd, name)
                fields[name] = elem
            else:
                inner_dict: typing.Dict[str, Element] = {}
                for sub_name, sub_node in nd.items():
                    if not isinstance(sub_node, dict):
                        raise TypeError(
                            f"Expected dict for '{name}.{sub_name}', got {type(sub_node)}"
                        )
                    inner_dict[sub_name] = element_from_mapping(
                        typing.cast(typing.Dict[str, typing.Any], sub_node), sub_name
                    )
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
