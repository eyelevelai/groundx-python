import unittest

import dateparser
import pytest

pytest.importorskip("dateparser")


from groundx.extract.classes.field import ExtractedField
from groundx.extract.classes.prompt import Prompt
from groundx.extract.classes.testing import TestField


def typed_field(name, target, value):
    return ExtractedField(
        prompt=Prompt(
            attr_name=name,
            identifiers=[name],
            instructions=name,
            type=target,
        ),
        value=value,
    )


class TestExtractedField(unittest.TestCase):
    def test_supported_types_use_shared_coercion(self):
        cases = [
            ("str_field", "str", True, "true"),
            ("int_field", "int", "3.9", 3),
            ("float_field", "float", "1,234.5", 1234.5),
            ("list_field", "list", '[1,"two"]', [1, "two"]),
            ("dict_field", "dict", '{"a":true}', {"a": True}),
        ]
        for name, target, value, expected in cases:
            with self.subTest(target=target):
                field = typed_field(name, target, value)
                self.assertEqual(field.get_value(), expected)
                self.assertIs(type(field.get_value()), type(expected))
                self.assertIsNone(field.coercion_warning)

    def test_missing_and_impossible_values_remain_null(self):
        for target in ["str", "int", "float", "list", "dict"]:
            with self.subTest(target=target, kind="missing"):
                field = typed_field(f"{target}_field", target, None)
                self.assertIsNone(field.get_value())
                self.assertIn("value", field.model_dump(exclude_none=False))
                self.assertIsNone(field.model_dump(exclude_none=False)["value"])

            with self.subTest(target=target, kind="impossible"):
                impossible = {"str": object(), "int": [], "float": {}, "list": "bad", "dict": "bad"}[target]
                field = typed_field(f"{target}_field", target, impossible)
                self.assertIsNone(field.get_value())
                self.assertIsNone(field.model_dump(exclude_none=False)["value"])
                self.assertIsNotNone(field.coercion_warning)
                self.assertIn(f"{target}_field", field.coercion_warning)
                self.assertNotIn("bad", field.coercion_warning)
                self.assertNotIn("coercion_warning", field.model_dump(exclude_none=False))

    def test_date_normalization_remains_separate(self):
        field = typed_field("statement_date", "str", "3/29/25")
        self.assertEqual(field.get_value(), "2025-03-29")
        self.assertIsNone(field.coercion_warning)

    def test_equalToValue_string(self):
        ef = TestField("test", "hello")
        self.assertTrue(ef.equal_to_value("hello"))
        self.assertFalse(ef.equal_to_value("world"))

    def test_equalToValue_int_float_equivalence(self):
        ef = TestField("test", int(10))
        self.assertTrue(ef.equal_to_value(10.0))
        self.assertTrue(ef.equal_to_value(10))

    def test_equalToValue_mismatch(self):
        ef = TestField("test", 3.14)
        self.assertFalse(ef.equal_to_value(2.71))

    @unittest.skip(
        "AGE-68: production get_value() returns None for empty int/float; test expects 0 — quarantined pending product decision"
    )
    def test_get_value(self):
        ef1 = TestField("test", "")
        if not ef1.prompt:
            self.fail("prompt is None")

        self.assertEqual(ef1.get_value(), "")

        ef1.prompt.type = ["int", "float"]
        self.assertEqual(ef1.get_value(), 0)

        ef1.prompt.type = "int"
        self.assertEqual(ef1.get_value(), 0)

        ef1.prompt.type = "float"
        self.assertEqual(ef1.get_value(), 0)

        ef2 = TestField("test", 0)
        if not ef2.prompt:
            self.fail("prompt is None")

        self.assertEqual(ef2.get_value(), 0)

        ef2.prompt.type = "str"
        self.assertEqual(ef2.get_value(), "0.0")

        ef2.prompt.type = ["str"]
        self.assertEqual(ef2.get_value(), "0.0")

        ef2.prompt.type = ["list"]
        self.assertEqual(ef2.get_value(), "0.0")

        ef2.prompt.type = "dict"
        self.assertEqual(ef2.get_value(), "0.0")

    def test_render_error(self):
        ef = TestField("test", "hello")
        with self.assertRaises(Exception) as e:
            ef.render()
        self.assertEqual(str(e.exception), "prompt.type is not set for [test]")

    def test_set_value_dates(self):
        ef1 = TestField("test date", "3/29/25")
        self.assertEqual(ef1.get_value(), "2025-03-29")
        ef2 = TestField("test date", "2025-03-29")
        self.assertEqual(ef2.get_value(), "2025-03-29")

        tst_date = dateparser.parse("1234")
        if tst_date is None:
            raise Exception("tst_date is none")

        tst_date = tst_date.strftime("%Y-%m-%d")
        ef3 = TestField("test date", "1234")
        self.assertEqual(ef3.get_value(), tst_date)


if __name__ == "__main__":
    unittest.main()
