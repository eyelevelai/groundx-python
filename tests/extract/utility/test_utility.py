import json
import typing
import unittest

from groundx.extract.classes.prompt import Prompt
from groundx.extract.utility.utility import (
    CoercionResult,
    clean_json,
    coerce_numeric_string,
    coerce_value,
    validate_confidence,
)


class TestUtilCleanJson(unittest.TestCase):
    def test_trims_only_unmatched_trailing_json_closers(self) -> None:
        cleaned = clean_json('{"plan_name": "Example", "items": [1, 2]}]')

        self.assertEqual(
            json.loads(cleaned),
            {"plan_name": "Example", "items": [1, 2]},
        )

    def test_preserves_trailing_non_json_text(self) -> None:
        self.assertEqual(clean_json('{"plan_name": "Example"} thanks'), '{"plan_name": "Example"} thanks')


class TestUtilCoerceNumericString(unittest.TestCase):
    def test_expected_str(self) -> None:
        # When expected type is str, no coercion occurs
        self.assertEqual(coerce_numeric_string("42", "str"), "42")
        self.assertEqual(coerce_numeric_string("foo", "str"), "foo")
        self.assertEqual(coerce_numeric_string(7, "str"), "7")
        self.assertEqual(coerce_numeric_string(2.71, "str"), "2.71")
        self.assertEqual(coerce_numeric_string(0, "str"), "0")

    def test_expected_int(self) -> None:
        # Numeric string to int or float based on content
        self.assertEqual(coerce_numeric_string("42", "int"), 42)
        self.assertEqual(coerce_numeric_string("3.14", "int"), 3)
        self.assertIsNone(coerce_numeric_string("foo", "int"))
        self.assertEqual(coerce_numeric_string(8, "int"), 8)
        self.assertEqual(coerce_numeric_string(3.14, "int"), 3)
        self.assertIsNone(coerce_numeric_string("", "int"))
        self.assertEqual(coerce_numeric_string("0", "int"), 0)

    def test_expected_float(self) -> None:
        self.assertEqual(coerce_numeric_string("42", "float"), 42.0)
        self.assertEqual(coerce_numeric_string("3.14", "float"), 3.14)
        self.assertIsNone(coerce_numeric_string("foo", "float"))
        self.assertEqual(coerce_numeric_string(9.81, "float"), 9.81)
        self.assertEqual(coerce_numeric_string(10, "float"), 10)
        self.assertIsNone(coerce_numeric_string("", "float"))
        self.assertEqual(coerce_numeric_string("0.0", "float"), 0.0)

    def test_expected_int_float_list(self) -> None:
        types: typing.List[str] = ["int", "float"]
        self.assertEqual(coerce_numeric_string("42", types), 42)
        self.assertEqual(coerce_numeric_string("3.14", types), 3.14)
        self.assertIsNone(coerce_numeric_string("foo", types))
        self.assertEqual(coerce_numeric_string(11, types), 11)
        self.assertEqual(coerce_numeric_string(2.718, types), 2.718)
        self.assertEqual(coerce_numeric_string("0.00", types), 0.0)
        self.assertIsNone(coerce_numeric_string("", types))


class TestUtilCoerceValue(unittest.TestCase):
    def assert_result(
        self,
        result: CoercionResult,
        value: typing.Any,
        expected_type: typing.Optional[type],
        matched: bool,
        converted: bool,
    ) -> None:
        self.assertEqual(result.value, value)
        if expected_type is not None:
            self.assertIs(type(result.value), expected_type)
        self.assertIs(result.matched, matched)
        self.assertIs(result.converted, converted)
        if matched:
            self.assertIsNone(result.warning)
        else:
            self.assertIsNotNone(result.warning)

    def test_exact_values_and_null_are_preserved(self) -> None:
        cases: typing.List[typing.Tuple[typing.Any, typing.Union[str, typing.List[str]]]] = [
            ("text", "str"),
            (7, "int"),
            (7.5, "float"),
            ([1], "list"),
            ({"a": 1}, "dict"),
            (7, ["float", "int"]),
        ]
        for value, target in cases:
            with self.subTest(value=value, target=target):
                self.assert_result(coerce_value(value, target), value, type(value), True, False)

        self.assert_result(coerce_value(None, "str"), None, type(None), True, False)
        self.assert_result(coerce_value(None, ["int", "float"]), None, type(None), True, False)
        self.assert_result(coerce_value({"a": 1}), {"a": 1}, dict, True, False)

    def test_scalar_conversions_are_deterministic(self) -> None:
        cases = [
            (True, "str", "true", str, True),
            (False, "str", "false", str, True),
            (7, "str", "7", str, True),
            (7.5, "str", "7.5", str, True),
            ("0", "str", "0", str, False),
            ("1,234", "int", 1234, int, True),
            ("3.9", "int", 3, int, True),
            ("-3.9", "int", -3, int, True),
            ("1,234.5", "float", 1234.5, float, True),
            (8, "float", 8.0, float, True),
            (8.9, "int", 8, int, True),
        ]
        for value, target, expected, expected_type, converted in cases:
            with self.subTest(value=value, target=target):
                self.assert_result(coerce_value(value, target), expected, expected_type, True, converted)

    def test_container_conversions_use_json(self) -> None:
        cases = [
            ([1, "two"], "str", '[1,"two"]', str),
            ({"a": True}, "str", '{"a":true}', str),
            ('[1,"two"]', "list", [1, "two"], list),
            ('{"a":true}', "dict", {"a": True}, dict),
        ]
        for value, target, expected, expected_type in cases:
            with self.subTest(value=value, target=target):
                self.assert_result(coerce_value(value, target), expected, expected_type, True, True)

    def test_numeric_union_preserves_exact_values_and_parses_by_content(self) -> None:
        self.assert_result(coerce_value("42", ["int", "float"]), 42, int, True, True)
        self.assert_result(coerce_value("3.14", ["int", "float"]), 3.14, float, True, True)
        self.assert_result(coerce_value(3.14, ["int", "float"]), 3.14, float, True, False)
        self.assert_result(coerce_value(3, ["float", "int"]), 3, int, True, False)

    def test_integer_text_does_not_lose_precision_through_float(self) -> None:
        self.assert_result(
            coerce_value("9007199254740993", "int"),
            9007199254740993,
            int,
            True,
            True,
        )

    def test_excessive_integer_exponent_is_unmatched(self) -> None:
        self.assert_result(
            coerce_value("1e100000000", "int"),
            None,
            type(None),
            False,
            False,
        )

    def test_non_finite_numeric_text_is_unmatched(self) -> None:
        cases = [
            ("1e100000000", "float"),
            ("1e100000000", ["int", "float"]),
            (float("inf"), "float"),
        ]
        for value, target in cases:
            with self.subTest(value=value, target=target):
                self.assert_result(
                    coerce_value(value, target),
                    None,
                    type(None),
                    False,
                    False,
                )

    def test_union_with_unknown_target_is_unmatched(self) -> None:
        self.assert_result(
            coerce_value("text", ["str", "unsupported"]),
            None,
            type(None),
            False,
            False,
        )

    def test_impossible_conversions_return_content_free_warning(self) -> None:
        cases = [
            (True, "int", "bool", "int"),
            (False, "float", "bool", "float"),
            ("", "int", "str", "int"),
            ("secret value", "float", "str", "float"),
            ([1], "int", "list", "int"),
            ({"a": 1}, "float", "dict", "float"),
            ("not json", "list", "str", "list"),
            ('{"a":1}', "list", "str", "list"),
            ("[1]", "dict", "str", "dict"),
            ("secret value", "date", "str", "date"),
        ]
        for value, target, source_name, target_name in cases:
            with self.subTest(value=value, target=target):
                result = coerce_value(value, target)
                self.assert_result(result, None, type(None), False, False)
                assert result.warning is not None
                self.assertIn(source_name, result.warning)
                self.assertIn(target_name, result.warning)
                self.assertNotIn("secret value", result.warning)


class TestValidateConfidence(unittest.TestCase):
    def test_uses_shared_conversion_without_warning_on_success(self) -> None:
        prompt = Prompt(attr_name="enabled", instructions="enabled", type="str")

        value, confidence, warning = validate_confidence(
            "enabled",
            prompt,
            {"enabled"},
            {"value": True, "confidence": "high"},
            {},
        )

        self.assertEqual((value, confidence, warning), ("true", "high", None))

    def test_unmatched_value_returns_null_and_field_scoped_warning(self) -> None:
        prompt = Prompt(attr_name="amount", instructions="amount", type="float")

        value, confidence, warning = validate_confidence(
            "amount",
            prompt,
            {"amount"},
            {"value": "private text", "confidence": "high"},
            {},
        )

        self.assertIsNone(value)
        self.assertIsNone(confidence)
        self.assertIsNotNone(warning)
        assert warning is not None
        self.assertIn("amount", warning)
        self.assertIn("str", warning)
        self.assertIn("float", warning)
        self.assertNotIn("private text", warning)


if __name__ == "__main__":
    unittest.main()
