import unittest

from .element import Element
from .group import Group
from .prompt import Prompt


class TestGroup(unittest.TestCase):
    def test_model_dump_json_1(self) -> None:
        grp = Group(
            fields={
                "account_number": Element(
                    prompt=Prompt(full="account_number"),
                ),
            },
        )
        self.assertEqual(
            grp.model_dump_json(exclude_none=True),
            '{"account_number":{"prompt":{"full":"account_number","required":false}}}',
        )

    def test_model_validate_json_1(self) -> None:
        grp = Group(
            fields={
                "account_number": Element(
                    prompt=Prompt(full="account_number"),
                ),
            },
        )
        self.assertEqual(
            Group.model_validate_json(
                '{"account_number":{"prompt":{"full":"account_number"}}}'
            ),
            grp,
        )

    def test_model_validate_json_2(self) -> None:
        grp = Group(
            fields={
                "account_number": Element(
                    prompt=Prompt(full="account_number"),
                ),
            },
        )
        self.assertEqual(
            Group.model_validate_json(
                '{"fields":{"account_number":{"prompt":{"full":"account_number"}}}}'
            ),
            grp,
        )

    def test_model_validate_json_3(self) -> None:
        grp = Group(
            fields={
                "account_number": Element(
                    prompt=Prompt(full="account_number_1"),
                ),
            },
        )
        self.assertEqual(
            Group.model_validate_json(
                '{"account_number":{"prompt":{"full":"account_number_1"}},"fields":{"account_number":{"prompt":{"full":"account_number_2"}}},"statement_date":null}'
            ),
            grp,
        )
