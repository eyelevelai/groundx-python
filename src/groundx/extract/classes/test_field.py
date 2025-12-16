import dateparser, pytest, typing, unittest

pytest.importorskip("dateparser")


from .field import ExtractedField
from .prompt import Prompt


def TestField(
    name: str,
    value: typing.Union[str, float, typing.List[typing.Any]],
    conflicts: typing.List[typing.Any] = [],
) -> ExtractedField:
    return ExtractedField(
        prompt=Prompt(
            attr_name=name.replace("_", " "),
            identifiers=[name],
            instructions=name.replace("_", " "),
        ),
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
