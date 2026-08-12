import dataclasses
import json
import math
import typing


@dataclasses.dataclass(frozen=True)
class CoercionResult:
    value: typing.Any
    matched: bool
    converted: bool
    warning: typing.Optional[str] = None


_SUPPORTED_TYPES: typing.Dict[str, typing.Type[typing.Any]] = {
    "str": str,
    "int": int,
    "float": float,
    "list": list,
    "dict": dict,
}


def _coercion_warning(value: typing.Any, targets: typing.Sequence[str]) -> str:
    target_names = ", ".join(targets) if targets else "unsupported"
    return f"cannot coerce {type(value).__name__} to {target_names}"


def _coerce_to_type(value: typing.Any, target: str) -> typing.Tuple[typing.Any, bool]:
    target_type = _SUPPORTED_TYPES[target]

    if target_type is str:
        if type(value) in (bool, int, float, list, dict):
            return json.dumps(value, separators=(",", ":")), True
        return None, False

    if target_type in (int, float):
        if type(value) is bool or type(value) in (list, dict):
            return None, False
        if type(value) is str:
            normalized = value.replace(",", "")
            if not normalized:
                return None, False
            try:
                number: typing.Union[int, float]
                if target_type is int and not any(char in normalized for char in ".eE"):
                    number = int(normalized)
                else:
                    number = float(normalized)
            except (OverflowError, ValueError):
                return None, False
        elif type(value) in (int, float):
            number = value
        else:
            return None, False

        if type(number) is float and not math.isfinite(number):
            return None, False

        try:
            if target_type is int:
                return int(number), True
            return float(number), True
        except (OverflowError, ValueError):
            return None, False

    if target_type in (list, dict) and type(value) is str:
        try:
            decoded = json.loads(value)
        except (json.JSONDecodeError, RecursionError):
            return None, False
        if type(decoded) is target_type:
            return decoded, True

    return None, False


def coerce_value(
    value: typing.Any,
    expected_types: typing.Optional[typing.Union[str, typing.List[str]]] = None,
) -> CoercionResult:
    if not expected_types:
        return CoercionResult(value=value, matched=True, converted=False)

    targets = [expected_types] if isinstance(expected_types, str) else expected_types
    if not isinstance(targets, list) or not all(isinstance(target, str) for target in targets):
        return CoercionResult(
            value=None,
            matched=False,
            converted=False,
            warning=_coercion_warning(value, []),
        )

    supported_targets = [target for target in targets if target in _SUPPORTED_TYPES]
    if len(supported_targets) != len(targets):
        return CoercionResult(
            value=None,
            matched=False,
            converted=False,
            warning=_coercion_warning(value, targets),
        )

    if type(value) is float and not math.isfinite(value):
        return CoercionResult(
            value=None,
            matched=False,
            converted=False,
            warning=_coercion_warning(value, targets),
        )

    for target in supported_targets:
        if type(value) is _SUPPORTED_TYPES[target]:
            return CoercionResult(value=value, matched=True, converted=False)

    if value is None:
        return CoercionResult(value=None, matched=True, converted=False)

    conversion_order = supported_targets
    if set(supported_targets) == {"int", "float"} and type(value) is str:
        normalized = value.replace(",", "")
        conversion_order = ["float", "int"] if any(char in normalized for char in ".eE") else ["int", "float"]

    for target in conversion_order:
        try:
            converted_value, converted = _coerce_to_type(value, target)
        except (RecursionError, TypeError, ValueError):
            continue
        if converted:
            return CoercionResult(value=converted_value, matched=True, converted=True)

    return CoercionResult(
        value=None,
        matched=False,
        converted=False,
        warning=_coercion_warning(value, targets),
    )


def _complete_json_document_end(txt: str) -> typing.Optional[int]:
    stack: typing.List[str] = []
    in_string = False
    escaped = False
    started = False

    for idx, char in enumerate(txt):
        if not started:
            if char.isspace():
                continue
            if char == "{":
                stack.append("}")
                started = True
                continue
            if char == "[":
                stack.append("]")
                started = True
                continue
            return None

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in "}]":
            if not stack:
                return idx
            if char != stack[-1]:
                return None
            stack.pop()
            if not stack:
                return idx + 1

    return None


def clean_json(txt: str) -> str:
    for p in ("json```\n", "```json\n", "json\n"):
        if txt.startswith(p):
            txt = txt[len(p) :]
    if txt.endswith("```"):
        txt = txt[:-3]
    txt = txt.strip()
    document_end = _complete_json_document_end(txt)
    if document_end is not None and document_end < len(txt):
        trailing = txt[document_end:].strip()
        if trailing and all(char in "}]" for char in trailing):
            txt = txt[:document_end]
    return txt.strip()


def coerce_numeric_string(
    value: typing.Any,
    et: typing.Optional[typing.Union[str, typing.List[str]]] = None,
) -> typing.Optional[typing.Union[int, float, typing.Any]]:
    return coerce_value(value, et).value


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
        return tys

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
            f"field {key_data.attr_name}: expected confidence object, got {type(value).__name__}",
        )

    if "value" not in value:
        return (
            None,
            None,
            f"field {key_data.attr_name}: confidence object is missing value",
        )

    if value["value"] is None:
        return None, None, None

    result = coerce_value(value["value"], key_data.type)
    final_value = result.value
    if not result.matched:
        return (
            final_value,
            None,
            f"field {key_data.attr_name}: {result.warning}",
        )

    if "confidence" not in value:
        return (
            final_value,
            None,
            f"field {key_data.attr_name}: confidence object is missing confidence",
        )

    if not isinstance(value["confidence"], str):
        return (
            final_value,
            None,
            f"field {key_data.attr_name}: confidence must be str, got {type(value['confidence']).__name__}",
        )

    if value["confidence"] not in ["low", "medium", "high"]:
        return (
            final_value,
            None,
            f"field {key_data.attr_name}: confidence is unsupported",
        )

    return final_value, value["confidence"], None
