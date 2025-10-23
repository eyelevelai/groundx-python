import typing

if typing.TYPE_CHECKING:
    from ..classes.prompt import Prompt


def class_fields(cls: typing.Any) -> typing.Set[str]:
    fields: typing.Set[str] = set()
    if hasattr(cls, "model_fields"):
        fields = set(cls.model_fields.keys())
    elif hasattr(cls, "__fields__"):
        fields = set(cls.__fields__.keys())  # type: ignore[reportDeprecated]
    else:
        fields = set()

    return fields


def clean_json(txt: str) -> str:
    for p in ("json```\n", "```json\n", "json\n"):
        if txt.startswith(p):
            txt = txt[len(p) :]
    if txt.endswith("```"):
        txt = txt[:-3]
    return txt.strip()


def coerce_numeric_string(
    value: typing.Any,
    et: typing.Union[str, typing.List[str]],
) -> typing.Union[typing.Any, typing.List[typing.Any]]:
    expected_types = str_to_type_sequence(et)

    if any(t in (int, float) for t in expected_types):
        if isinstance(value, str):
            value = value.replace(",", "")
            try:
                value = float(value)
            except ValueError:
                return value
        if float in expected_types:
            return value
        return int(value)

    if str in expected_types and isinstance(value, str) and value == "0":
        return None

    return value


def from_attr_name(
    name: str, prompts: typing.Sequence[typing.Mapping[str, "Prompt"]]
) -> typing.Tuple[typing.Optional[str], typing.Optional[typing.Any]]:
    for pmps in prompts:
        for key, prompt in pmps.items():
            if getattr(prompt, "attr_name", None) == name:
                return key, prompt

    return None, None


def from_key(
    name: str,
    prompts: typing.Sequence[typing.Mapping[str, "Prompt"]],
) -> typing.Tuple[typing.Optional[str], typing.Optional[typing.Any]]:
    for pmps in prompts:
        for k, prompt in pmps.items():
            if k == name:
                return k, prompt

    key, pmp = from_attr_name(name, prompts)
    if pmp:
        return key, pmp

    return None, None


def str_to_type_sequence(
    ty: typing.Union[str, typing.List[str]],
) -> typing.Sequence[typing.Type[typing.Any]]:
    if isinstance(ty, list):
        tys: typing.List[typing.Any] = []
        for t in ty:
            tys.append(str_to_type(t))

        return tys

    return [str_to_type(ty)]


def str_to_type(
    ty: str,
) -> typing.Type[typing.Any]:
    if ty == "int":
        return int
    elif ty == "float":
        return float
    elif ty == "list":
        return list
    elif ty == "dict":
        return dict

    return str


def type_to_str(
    ty: typing.Union[typing.Type[typing.Any], typing.Sequence[typing.Type[typing.Any]]],
) -> typing.Union[str, typing.List[str]]:
    if isinstance(ty, list):
        tys: typing.List[str] = []
        for t in ty:
            nt = type_to_str(t)
            if isinstance(nt, str):
                tys.append(nt)
            else:
                tys.append("list")

    if ty == int:
        return "int"
    if ty == float:
        return "float"
    if ty == list:
        return "list"
    if ty == dict:
        return "dict"

    return "str"


def validate_confidence(
    key: str,
    key_data: typing.Any,
    fields: typing.Set[str],
    value: typing.Any,
    errors: typing.Dict[str, str],
) -> typing.Tuple[
    typing.Union[typing.Any, typing.List[typing.Any]],
    typing.Optional[str],
    typing.Optional[str],
]:
    if key_data.attr_name not in fields:
        return None, None, f"unexpected attribute [{key_data.attr_name}]"

    if value is None:
        return None, None, None

    if not isinstance(value, dict):
        return (
            None,
            None,
            f"unexpected value type [{key_data.attr_name}] [{type(value)}] [{key_data.type}]\n[{value}]",
        )

    if "value" not in value:
        return (
            None,
            None,
            f'value is missing "value" key [{key_data.attr_name}]\n[{value}]',
        )

    if value["value"] is None:
        return None, None, None

    final_value = coerce_numeric_string(value["value"], key_data.type)
    if not key_data.valid_value(final_value):
        return (
            final_value,
            None,
            f"unexpected type for statement [{key}] value [{type(final_value)}]\n\n{final_value}",
        )

    if "confidence" not in value:
        return (
            final_value,
            None,
            f'value is missing "confidence" key [{key_data.attr_name}]\n[{value}]',
        )

    if not isinstance(value["confidence"], str):
        return (
            final_value,
            None,
            f"confidence is not type str [{key_data.attr_name}]\n[{value}]",
        )

    if value["confidence"] not in ["low", "medium", "high"]:
        return (
            final_value,
            None,
            f'confidence value is unsupported value [{key_data.attr_name}]\n[{value["confidence"]}]',
        )

    return final_value, value["confidence"], None
