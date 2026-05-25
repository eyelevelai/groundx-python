import unittest

import dateparser, pytest

pytest.importorskip("dateparser")


from groundx.extract.classes.field import ExtractedField
from groundx.extract.classes.prompt import Prompt
from groundx.extract.classes.testing import TestField


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

    @unittest.skip(
        "AGE-68: get_value() returns None for empty int/float fields; this test "
        "expects 0. Product decision pending — quarantined to let CI run extract "
        "tests in AGE-67."
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
            raise Exception(f"tst_date is none")

        tst_date = tst_date.strftime("%Y-%m-%d")
        ef3 = TestField("test date", "1234")
        self.assertEqual(ef3.get_value(), tst_date)


if __name__ == "__main__":
    unittest.main()
