import unittest

from .manager import load_from_yaml, PromptManager
from .source import Source
from ..classes.element import Element
from ..classes.group import Group
from ..classes.prompt import Prompt


SAMPLE_YAML = """
fields:
  statement_date:
    prompt:
      description: date when the invoice was computed or sent to the customer
      prompt: |
        ## statement_date
      type: str
  meters:
    prompt:
      prompt: |
        ## meters
    fields:
      meter_number:
        prompt:
          description: unique identifier for the meter that made the utility service measurement
          prompt: |
            ## meter_number
          type: str
"""


class TestSource(Source):
    def __init__(self, raw: str, version: str = "v1") -> None:
        self._raw = raw
        self._version = version

    def fetch(self) -> tuple[str, str]:
        return self._raw, self._version

    def peek(self) -> tuple[str, str]:
        return self._raw, self._version

    def update(self, raw: str, version: str) -> None:
        self._raw = raw
        self._version = version


class Test_load_from_yaml(unittest.TestCase):
    def test_load_root_group_from_yaml_structure(self) -> None:
        root = load_from_yaml(SAMPLE_YAML)

        # Root is a Group
        self.assertIsInstance(root, Group)

        # Top-level fields
        self.assertIn("statement_date", root.fields)
        self.assertIn("meters", root.fields)

        statement_date = root.fields["statement_date"]
        meters = root.fields["meters"]

        # statement_date should be an Element with a Prompt
        self.assertIsInstance(statement_date, Element)

        if isinstance(statement_date, Element):
            self.assertIsNotNone(statement_date.prompt)
            if statement_date.prompt:
                self.assertEqual(
                    statement_date.prompt.description,
                    "date when the invoice was computed or sent to the customer",
                )
                self.assertIn("## statement_date", statement_date.prompt.prompt)

        # meters should be a Group with nested fields
        self.assertIsInstance(meters, Group)

        if isinstance(meters, Group):
            self.assertIn("meter_number", meters.fields)

            meter_number = meters.fields["meter_number"]
            self.assertIsInstance(meter_number, Element)

            if isinstance(meter_number, Element):
                self.assertIsNotNone(meter_number.prompt)

                if meter_number.prompt:
                    self.assertEqual(
                        meter_number.prompt.description,
                        "unique identifier for the meter that made the utility service measurement",
                    )
                    self.assertIn("## meter_number", meter_number.prompt.prompt)

    def test_prompt_manager_builds_flat_prompt_dict(self) -> None:
        source = TestSource(SAMPLE_YAML, version="v1")
        manager = PromptManager(config_source=source)

        fields = manager.fields

        self.assertIn("statement_date", fields)
        self.assertIsInstance(fields["statement_date"], Prompt)
        self.assertIn("## statement_date", fields["statement_date"].prompt)

        self.assertIn("meters", fields)
        self.assertIsInstance(fields["meters"], Prompt)
        self.assertIn("## meters", fields["meters"].prompt)

        self.assertIn("meters.meter_number", fields)
        self.assertIsInstance(fields["meters.meter_number"], Prompt)
        self.assertIn("## meter_number", fields["meters.meter_number"].prompt)

    def test_reload_if_changed_updates_prompts(self) -> None:
        source = TestSource(SAMPLE_YAML, version="v1")
        manager = PromptManager(config_source=source)
        initial_fields = manager.fields

        self.assertIn("statement_date", initial_fields)
        self.assertIn("## statement_date", initial_fields["statement_date"].prompt)

        updated_yaml = SAMPLE_YAML.replace(
            "## statement_date", "## updated_statement_date"
        )
        source.update(updated_yaml, version="v2")

        manager.reload_if_changed()
        updated_fields = manager.fields

        self.assertIn("statement_date", updated_fields)
        self.assertIn(
            "## updated_statement_date", updated_fields["statement_date"].prompt
        )
