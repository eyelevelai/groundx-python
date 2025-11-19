import typing


from .prompt import Prompt


def from_attr_name(
    name: str, prompts: typing.Sequence[typing.Mapping[str, Prompt]]
) -> typing.Optional[typing.Any]:
    for pmps in prompts:
        for _, prompt in pmps.items():
            if prompt.attr_name and prompt.attr_name == name:
                return prompt

    return None


def from_key(
    name: str,
    prompts: typing.Sequence[typing.Mapping[str, Prompt]],
) -> typing.Optional[typing.Any]:
    for pmps in prompts:
        for _, prompt in pmps.items():
            if prompt.key() == name:
                return prompt

    return from_attr_name(name, prompts)
