import typing
import unittest

from groundx.extract.classes.prompt import Prompt


def TestPrompt(
    name: str,
    ty: typing.Union[str, typing.List[str]],
) -> Prompt:
    return Prompt(
        attr_name=name,
        identifiers=[name],
        instructions=name.replace("_", "-"),
        type=ty,
    )


class TestPromptValidValue(unittest.TestCase):
    def test_single_type_str(self):
        p = TestPrompt("field1", "str")
        self.assertTrue(p.valid_value("hello"))
        self.assertFalse(p.valid_value(123))
        self.assertFalse(p.valid_value((1, 2, 3)))
        self.assertFalse(p.valid_value([1, 2, 3]))

    def test_single_type_int(self):
        p = TestPrompt("field1", "int")
        self.assertFalse(p.valid_value("hello"))
        self.assertTrue(p.valid_value(123))
        self.assertFalse(p.valid_value(12.3))
        self.assertFalse(p.valid_value(True))
        self.assertFalse(p.valid_value((1, 2, 3)))
        self.assertFalse(p.valid_value([1, 2, 3]))

    def test_single_type_float(self):
        p = TestPrompt("field1", "float")
        self.assertFalse(p.valid_value("hello"))
        self.assertFalse(p.valid_value(123))
        self.assertTrue(p.valid_value(12.3))
        self.assertTrue(p.valid_value(123.0))
        self.assertFalse(p.valid_value(False))
        self.assertFalse(p.valid_value((1, 2, 3)))
        self.assertFalse(p.valid_value([1, 2, 3]))

    def test_single_type_bool(self):
        p = TestPrompt("field1", "bool")
        self.assertTrue(p.valid_value(True))
        self.assertTrue(p.valid_value(False))
        self.assertFalse(p.valid_value(1))
        self.assertFalse(p.valid_value("true"))

    def test_single_type_list(self):
        p = TestPrompt("field1", "list")
        self.assertFalse(p.valid_value("hello"))
        self.assertFalse(p.valid_value(123))
        self.assertFalse(p.valid_value(12.3))
        self.assertFalse(p.valid_value(123.0))
        self.assertFalse(p.valid_value((1, 2, 3)))
        self.assertTrue(p.valid_value([1, 2, 3]))

    def test_list_of_types_success_and_failure(self):
        p = TestPrompt("field2", ["str", "float"])
        self.assertTrue(p.valid_value("hello"))
        self.assertFalse(p.valid_value(123))
        self.assertTrue(p.valid_value(12.3))
        self.assertTrue(p.valid_value(123.0))
        self.assertFalse(p.valid_value((1, 2, 3)))
        self.assertFalse(p.valid_value([1, 2, 3]))

    def test_container_and_numeric_union_types_are_exact(self):
        self.assertTrue(TestPrompt("field", "dict").valid_value({"a": 1}))
        self.assertFalse(TestPrompt("field", "dict").valid_value([1]))
        numeric = TestPrompt("field", ["int", "float"])
        self.assertTrue(numeric.valid_value(1))
        self.assertTrue(numeric.valid_value(1.5))
        self.assertFalse(numeric.valid_value(True))
        self.assertFalse(TestPrompt("field", "date").valid_value("2025-01-01"))

    def test_repr_contains_fields(self):
        p = TestPrompt("field_5", "int")
        rep = repr(p)
        self.assertIn("field_5", rep)
        self.assertIn("field-5", rep)


if __name__ == "__main__":
    unittest.main()
