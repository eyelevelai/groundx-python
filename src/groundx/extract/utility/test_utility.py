import typing, unittest

from .utility import coerce_numeric_string


class TestUtilCoerceNumericString(unittest.TestCase):
    def test_expected_str(self) -> None:
        # When expected type is str, no coercion occurs
        self.assertEqual(coerce_numeric_string("42", "str"), "42")
        self.assertEqual(coerce_numeric_string("foo", "str"), "foo")
        self.assertEqual(coerce_numeric_string(7, "str"), 7)
        self.assertEqual(coerce_numeric_string(2.71, "str"), 2.71)

    def test_expected_int(self) -> None:
        # Numeric string to int or float based on content
        self.assertEqual(coerce_numeric_string("42", "int"), 42)
        self.assertEqual(coerce_numeric_string("3.14", "int"), 3)
        self.assertEqual(coerce_numeric_string("foo", "int"), "foo")
        self.assertEqual(coerce_numeric_string(8, "int"), 8)
        self.assertEqual(coerce_numeric_string(3.14, "int"), 3)

    def test_expected_float(self) -> None:
        self.assertEqual(coerce_numeric_string("42", "float"), 42.0)
        self.assertEqual(coerce_numeric_string("3.14", "float"), 3.14)
        self.assertEqual(coerce_numeric_string("foo", "float"), "foo")
        self.assertEqual(coerce_numeric_string(9.81, "float"), 9.81)
        self.assertEqual(coerce_numeric_string(10, "float"), 10)

    def test_expected_int_float_list(self) -> None:
        types: typing.List[str] = ["int", "float"]
        self.assertEqual(coerce_numeric_string("42", types), 42)
        self.assertEqual(coerce_numeric_string("3.14", types), 3.14)
        self.assertEqual(coerce_numeric_string("foo", types), "foo")
        self.assertEqual(coerce_numeric_string(11, types), 11)
        self.assertEqual(coerce_numeric_string(2.718, types), 2.718)


if __name__ == "__main__":
    unittest.main()
