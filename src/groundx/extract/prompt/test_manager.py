import typing, unittest

from .manager import load_from_yaml, PromptManager
from .source import Source
from ..classes.element import Element
from ..classes.group import Group


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
    def __init__(self, raw: str) -> None:
        self._raw: typing.Dict[str, str] = {
            "latest": raw,
        }

    def fetch(self, workflow_id: str) -> typing.Tuple[str, str]:
        wf = self._raw[workflow_id]

        return wf, workflow_id

    def peek(self, workflow_id: str) -> typing.Optional[str]:
        return workflow_id

    def update(self, raw: str, workflow_id: str) -> None:
        self._raw[workflow_id] = raw


class Test_load_from_yaml(unittest.TestCase):
    def test_load_from_yaml_structure(self) -> None:
        root = load_from_yaml(SAMPLE_YAML)

        self.assertIsInstance(root, Group)

        self.assertIn("statement_date", root.fields)
        self.assertIn("meters", root.fields)

        statement_date = root.fields["statement_date"]
        meters = root.fields["meters"]

        self.assertIsInstance(statement_date, Element)

        if isinstance(statement_date, Element):
            self.assertIsNotNone(statement_date.prompt)
            if statement_date.prompt:
                self.assertEqual(
                    statement_date.prompt.description,
                    "date when the invoice was computed or sent to the customer",
                )
                self.assertEqual(statement_date.prompt.attr_name, "statement_date")
                self.assertIn("## statement_date", statement_date.prompt.prompt)

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
                    self.assertEqual(meter_number.prompt.attr_name, "meter_number")
                    self.assertIn("## meter_number", meter_number.prompt.prompt)

    def test_prompt_manager_builds_flat_prompt_dict(self) -> None:
        source = TestSource(SAMPLE_YAML)
        manager = PromptManager(config_source=source)

        fields = manager.get_fields_for_workflow("latest")

        self.assertIn("meters", fields.fields)
        self.assertIn("statement_date", fields.fields)
        self.assertEqual(len(fields.fields), 2)

        sd = fields.fields["statement_date"]
        self.assertIsInstance(sd, Element)
        if isinstance(sd, Element):
            pmp = sd.prompt
            self.assertIsNotNone(pmp)
            if pmp:
                self.assertEqual(pmp.attr_name, "statement_date")
                self.assertIn("## statement_date", pmp.prompt)

        mtrs = fields.fields["meters"]
        self.assertIsInstance(mtrs, Group)
        if isinstance(mtrs, Group):
            pmp = mtrs.prompt
            self.assertIsNotNone(pmp)
            if pmp:
                self.assertEqual(pmp.attr_name, "meters")
                self.assertIn("## meters", pmp.prompt)

            self.assertEqual(len(mtrs.fields), 1)
            self.assertIn("meter_number", mtrs.fields)

            mn = mtrs.fields["meter_number"]
            self.assertIsInstance(mn, Element)
            if isinstance(mn, Element):
                pmp = mn.prompt
                self.assertIsNotNone(pmp)
                if pmp:
                    self.assertEqual(pmp.attr_name, "meter_number")
                    self.assertIn("## meter_number", pmp.prompt)

    def test_reload_if_changed_updates_prompts(self) -> None:
        source = TestSource(SAMPLE_YAML)
        manager = PromptManager(config_source=source)
        initial_fields = manager.get_fields_for_workflow("latest")

        self.assertIn("statement_date", initial_fields.fields)
        self.assertEqual(len(initial_fields.fields), 2)
        sd = initial_fields.fields["statement_date"]
        self.assertIsInstance(sd, Element)
        if isinstance(sd, Element):
            pmp = sd.prompt
            self.assertIsNotNone(pmp)
            if pmp:
                self.assertEqual(pmp.attr_name, "statement_date")
                self.assertIn("## statement_date", pmp.prompt)

        updated_yaml = SAMPLE_YAML.replace(
            "## statement_date", "## updated_statement_date"
        )
        source.update(updated_yaml, "v2")

        manager.reload_if_changed()
        updated_fields = manager.get_fields_for_workflow("v2")

        sd = updated_fields.fields["statement_date"]
        self.assertIsInstance(sd, Element)
        if isinstance(sd, Element):
            pmp = sd.prompt
            self.assertIsNotNone(pmp)
            if pmp:
                self.assertEqual(pmp.attr_name, "statement_date")
                self.assertIn("## updated_statement_date", pmp.prompt)
