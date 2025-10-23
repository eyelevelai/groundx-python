import pytest, typing, unittest

pytest.importorskip("dateparser")

from .field import ExtractedField


def TestField(
    name: str,
    value: typing.Union[str, float, typing.List[typing.Any]],
    conflicts: typing.List[typing.Any] = [],
) -> ExtractedField:
    return ExtractedField(
        key=name.replace("_", " "),
        value=value,
        conflicts=conflicts,
    )


class TestExtractedField(unittest.TestCase):
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

    def test_set_value_dates(self):
        ef1 = TestField("test date", "3/29/25")
        self.assertEqual(ef1.get_value(), "2025-03-29")
        ef2 = TestField("test date", "2025-03-29")
        self.assertEqual(ef2.get_value(), "2025-03-29")


if __name__ == "__main__":
    unittest.main()
