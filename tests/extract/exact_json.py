import json
import re
import typing


_SIMPLE_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _json_type(value: typing.Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def _object_path(path: str, key: str) -> str:
    if _SIMPLE_KEY.fullmatch(key):
        return f"{path}.{key}"
    return f"{path}[{json.dumps(key)}]"


def _present_difference(
    path: str,
    kind: str,
    side: str,
    value: typing.Any,
) -> dict[str, typing.Any]:
    return {
        side: value,
        f"{side}_type": _json_type(value),
        "kind": kind,
        "path": path,
    }


def exact_json_differences(
    actual: typing.Any,
    expected: typing.Any,
    path: str = "$",
) -> list[dict[str, typing.Any]]:
    actual_type = _json_type(actual)
    expected_type = _json_type(expected)
    if actual_type != expected_type:
        return [
            {
                "actual": actual,
                "actual_type": actual_type,
                "expected": expected,
                "expected_type": expected_type,
                "kind": "type",
                "path": path,
            }
        ]

    if isinstance(expected, dict):
        differences: list[dict[str, typing.Any]] = []
        for key in sorted(set(actual) | set(expected)):
            child_path = _object_path(path, key)
            if key not in actual:
                differences.append(
                    _present_difference(child_path, "missing", "expected", expected[key])
                )
            elif key not in expected:
                differences.append(
                    _present_difference(
                        child_path,
                        "unexpected",
                        "actual",
                        actual[key],
                    )
                )
            else:
                differences.extend(
                    exact_json_differences(actual[key], expected[key], child_path)
                )
        return differences

    if isinstance(expected, list):
        differences = []
        for index in range(max(len(actual), len(expected))):
            child_path = f"{path}[{index}]"
            if index >= len(actual):
                differences.append(
                    _present_difference(
                        child_path,
                        "missing",
                        "expected",
                        expected[index],
                    )
                )
            elif index >= len(expected):
                differences.append(
                    _present_difference(
                        child_path,
                        "unexpected",
                        "actual",
                        actual[index],
                    )
                )
            else:
                differences.extend(
                    exact_json_differences(actual[index], expected[index], child_path)
                )
        return differences

    if actual != expected:
        return [
            {
                "actual": actual,
                "actual_type": actual_type,
                "expected": expected,
                "expected_type": expected_type,
                "kind": "value",
                "path": path,
            }
        ]
    return []


def exact_json_report(
    actual: typing.Any,
    expected: typing.Any,
) -> dict[str, typing.Any]:
    differences = exact_json_differences(actual, expected)
    return {
        "differences": differences,
        "first_path": differences[0]["path"] if differences else None,
    }
