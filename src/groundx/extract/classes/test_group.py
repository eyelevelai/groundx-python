import unittest

from .element import Element
from .group import Group
from .prompt import Prompt


class TestGroup(unittest.TestCase):
    def test_model_dump_json_1(self) -> None:
        grp = Group(
            fields={
                "account_number": Element(
                    prompt=Prompt(
                        description="desc",
                        identifiers=["id"],
                        instructions="account_number",
                    ),
                ),
            },
        )
        self.assertEqual(
            grp.model_dump_json(exclude_none=True),
            '{"account_number":{"prompt":{"description":"desc","identifiers":["id"],"instructions":"account_number","required":false}}}',
        )

    def test_model_dump_json_2(self) -> None:
        grp = Group(
            fields={
                "account_number": Element(
                    prompt=Prompt(
                        description="desc",
                        identifiers=["id"],
                        instructions="account_number",
                    ),
                ),
            },
        )
        grp.remove_fields = False
        self.assertEqual(
            grp.model_dump_json(exclude_none=True),
            '{"fields":{"account_number":{"prompt":{"description":"desc","identifiers":["id"],"instructions":"account_number","required":false}}}}',
        )

    def test_model_validate_json_1(self) -> None:
        grp = Group(
            fields={
                "account_number": Element(
                    prompt=Prompt(
                        description="test",
                        identifiers=["id"],
                        instructions="account_number",
                    ),
                ),
            },
        )
        self.assertEqual(
            Group.model_validate_json(
                '{"account_number":{"prompt":{"description":"test","identifiers":["id"],"instructions":"account_number"}}}'
            ),
            grp,
        )

    def test_model_validate_json_2(self) -> None:
        grp = Group(
            fields={
                "account_number": Element(
                    prompt=Prompt(description="test", instructions="account_number"),
                ),
            },
        )
        self.assertEqual(
            Group.model_validate_json(
                '{"fields":{"account_number":{"prompt":{"description":"test","instructions":"account_number"}}}}'
            ),
            grp,
        )

    def test_model_validate_json_3(self) -> None:
        grp = Group(
            fields={
                "account_number": Element(
                    prompt=Prompt(description="desc1", instructions="account_number_1"),
                ),
            },
        )
        self.assertEqual(
            Group.model_validate_json(
                '{"account_number":{"prompt":{"description":"desc1","instructions":"account_number_1"}},"fields":{"account_number":{"prompt":{"description":"desc2","instructions":"account_number_2"}}},"statement_date":null}'
            ),
            grp,
        )
