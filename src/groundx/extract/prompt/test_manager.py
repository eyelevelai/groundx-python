import json, typing, unittest, yaml

from .manager import load_from_yaml, PromptManager
from .source import Source
from ..classes.field import ExtractedField
from ..classes.group import Group
from ..classes.prompt import Prompt


SAMPLE_YAML_1 = """
statement:
  fields:
    statement_date:
      prompt:
        description: date when the invoice was computed or sent to the customer
        format: YYYY-mm-dd date string
        identifiers:
          - Invoice Date
          - Billing Date
          - Account Summary as of XX/XX/XXXX
          - Bill Date
          - Account Balance as of XX/XX/XXXX
        instructions: |
          - **DO NOT INCLUDE THIS VALUE IF YOU CANNOT FIND AN EXPLICIT LABEL NEAR THE DATE**
        type: str
meters:
  prompt:
    instructions: |
      A meter is a total measurement of a utility service, charged by a utility provider, over some service period (a time period with a beginning and end).
  fields:
    meter_number:
      prompt:
        description: unique identifier for the meter that made the utility service measurement
        format: unique string, **always** formatted as a string
        identifiers:
          - "Meter #"
          - Meter ID
          - Premises Number
        instructions: |
          You must follow the following process to determine if you have found a valid meter number:
        type: str
    service_address:
      prompt:
        default: test address
        identifiers:
          - Premises Identifier
          - Premises Descriptor
        instructions: |
          - Strip the recipient name from the service address if it is a proper name, such as a person or company or municipality
        required: true
        type: str
"""

SAMPLE_YAML_2 = """
statement:
  fields:
    statement_date:
      prompt:
        description: date when the invoice was computed or sent to the customer
        identifiers:
          - Statement Date
        instructions: |
          ## statement_date
        type: str
    meters:
      prompt:
        instructions: |
          ## meters
      fields:
        meter_number:
          prompt:
            description: unique identifier for the meter that made the utility service measurement
            identifiers:
              - Meter Number
            instructions: |
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


class TestPromptManager(unittest.TestCase):
    def test_load_from_yaml_1(self) -> None:
        root = load_from_yaml(SAMPLE_YAML_1)

        self.assertIsInstance(root, dict)
        self.assertEqual(len(root), 2)

        self.assertIn("statement", root)
        self.assertIn("meters", root)
        self.assertIsInstance(root["statement"], Group)
        self.assertIsInstance(root["meters"], Group)
        self.assertEqual(len(root["statement"].fields), 1)
        self.assertEqual(len(root["meters"].fields), 2)

        self.assertIsNone(root["statement"].render())

        self.assertIn("statement_date", root["statement"].fields)
        statement_date = root["statement"].fields["statement_date"]
        self.assertIsInstance(statement_date, ExtractedField)

        if isinstance(statement_date, ExtractedField):
            check_prompt(
                self,
                statement_date.prompt,
                {
                    "attr_name": "statement_date",
                    "description": "date when the invoice was computed or sent to the customer",
                    "format": "YYYY-mm-dd date string",
                    "identifiers": [
                        "Invoice Date",
                        "Billing Date",
                        "Account Summary as of XX/XX/XXXX",
                        "Bill Date",
                        "Account Balance as of XX/XX/XXXX",
                    ],
                    "instructions": "- **DO NOT INCLUDE THIS VALUE IF YOU CANNOT FIND AN EXPLICIT LABEL NEAR THE DATE**\n",
                    "required": False,
                    "type": "str",
                },
            )
            self.assertEqual(
                """
## statement_date

Field:                  statement_date
Description:            date when the invoice was computed or sent to the customer
Format:                 YYYY-mm-dd date string
Example Identifiers:    Invoice Date, Billing Date, Account Summary as of XX/XX/XXXX, Bill Date, Account Balance as of XX/XX/XXXX
Special Instructions:
- **DO NOT INCLUDE THIS VALUE IF YOU CANNOT FIND AN EXPLICIT LABEL NEAR THE DATE**
""",
                statement_date.render(),
            )

        meters = root["meters"]
        check_prompt(
            self,
            meters.prompt,
            {
                "attr_name": "meters",
                "instructions": "A meter is a total measurement of a utility service, charged by a utility provider, over some service period (a time period with a beginning and end).\n",
                "required": False,
            },
        )
        self.assertEqual(
            """
# meters Definition

A meter is a total measurement of a utility service, charged by a utility provider, over some service period (a time period with a beginning and end).
""",
            meters.render(),
        )

        self.assertIn("meter_number", meters.fields)
        meter_number = meters.fields["meter_number"]
        self.assertIsInstance(meter_number, ExtractedField)

        if isinstance(meter_number, ExtractedField):
            check_prompt(
                self,
                meter_number.prompt,
                {
                    "attr_name": "meter_number",
                    "description": "unique identifier for the meter that made the utility service measurement",
                    "format": "unique string, **always** formatted as a string",
                    "identifiers": ["Meter #", "Meter ID", "Premises Number"],
                    "instructions": "You must follow the following process to determine if you have found a valid meter number:\n",
                    "required": False,
                    "type": "str",
                },
            )
            self.assertEqual(
                """
## meter_number

Field:                  meter_number
Description:            unique identifier for the meter that made the utility service measurement
Format:                 unique string, **always** formatted as a string
Example Identifiers:    Meter #, Meter ID, Premises Number
Special Instructions:
You must follow the following process to determine if you have found a valid meter number:
""",
                meter_number.render(),
            )

        self.assertIn("service_address", meters.fields)
        service_address = meters.fields["service_address"]
        self.assertIsInstance(service_address, ExtractedField)

        if isinstance(service_address, ExtractedField):
            check_prompt(
                self,
                service_address.prompt,
                {
                    "attr_name": "service_address",
                    "default": "test address",
                    "identifiers": ["Premises Identifier", "Premises Descriptor"],
                    "instructions": "- Strip the recipient name from the service address if it is a proper name, such as a person or company or municipality\n",
                    "required": True,
                    "type": "str",
                },
            )
            self.assertEqual(
                """
## service_address

Field:                  service_address
Default Value:          test address
Format:                 string
Example Identifiers:    Premises Identifier, Premises Descriptor
Special Instructions:
- Strip the recipient name from the service address if it is a proper name, such as a person or company or municipality
""",
                service_address.render(),
            )

    def test_load_from_yaml_2(self) -> None:
        root = load_from_yaml(SAMPLE_YAML_2)

        self.assertIsInstance(root, dict)
        self.assertEqual(len(root), 1)

        self.assertIn("statement", root)
        self.assertIsInstance(root["statement"], Group)
        self.assertEqual(len(root["statement"].fields), 2)

        self.assertIsNone(root["statement"].render())

        self.assertIn("statement_date", root["statement"].fields)
        statement_date = root["statement"].fields["statement_date"]
        self.assertIsInstance(statement_date, ExtractedField)

        if isinstance(statement_date, ExtractedField):
            check_prompt(
                self,
                statement_date.prompt,
                {
                    "attr_name": "statement_date",
                    "description": "date when the invoice was computed or sent to the customer",
                    "identifiers": ["Statement Date"],
                    "instructions": "## statement_date\n",
                    "required": False,
                    "type": "str",
                },
            )
            self.assertEqual(
                """
## statement_date

Field:                  statement_date
Description:            date when the invoice was computed or sent to the customer
Format:                 string
Example Identifiers:    Statement Date
Special Instructions:
## statement_date
""",
                statement_date.render(),
            )

        self.assertIn("meters", root["statement"].fields)
        meters = root["statement"].fields["meters"]
        self.assertIsInstance(meters, Group)
        if isinstance(meters, Group):
            check_prompt(
                self,
                meters.prompt,
                {
                    "attr_name": "meters",
                    "instructions": "## meters\n",
                    "required": False,
                },
            )
            self.assertEqual(
                """
# meters Definition

## meters
""",
                meters.render(),
            )

            self.assertIn("meter_number", meters.fields)
            meter_number = meters.fields["meter_number"]
            self.assertIsInstance(meter_number, ExtractedField)

            if isinstance(meter_number, ExtractedField):
                check_prompt(
                    self,
                    meter_number.prompt,
                    {
                        "attr_name": "meter_number",
                        "description": "unique identifier for the meter that made the utility service measurement",
                        "identifiers": ["Meter Number"],
                        "instructions": "## meter_number\n",
                        "required": False,
                        "type": "str",
                    },
                )
                self.assertEqual(
                    """
## meter_number

Field:                  meter_number
Description:            unique identifier for the meter that made the utility service measurement
Format:                 string
Example Identifiers:    Meter Number
Special Instructions:
## meter_number
""",
                    meter_number.render(),
                )

    def test_get_fields_for_workflow_1(self) -> None:
        source = TestSource(SAMPLE_YAML_1)
        manager = PromptManager(cache_source=source, config_source=source)

        root = manager.get_fields_for_workflow("latest")

        self.assertIsInstance(root, dict)
        self.assertEqual(len(root), 2)

        self.assertIn("statement", root)
        self.assertIn("meters", root)
        self.assertIsInstance(root["statement"], Group)
        self.assertIsInstance(root["meters"], Group)
        self.assertEqual(len(root["statement"].fields), 1)
        self.assertEqual(len(root["meters"].fields), 2)

        self.assertIn("statement_date", root["statement"].fields)
        statement_date = root["statement"].fields["statement_date"]
        self.assertIsInstance(statement_date, ExtractedField)

        if isinstance(statement_date, ExtractedField):
            pmp = statement_date.prompt
            self.assertIsNotNone(pmp)
            if pmp:
                self.assertEqual(pmp.attr_name, "statement_date")
            self.assertEqual(
                """
## statement_date

Field:                  statement_date
Description:            date when the invoice was computed or sent to the customer
Format:                 YYYY-mm-dd date string
Example Identifiers:    Invoice Date, Billing Date, Account Summary as of XX/XX/XXXX, Bill Date, Account Balance as of XX/XX/XXXX
Special Instructions:
- **DO NOT INCLUDE THIS VALUE IF YOU CANNOT FIND AN EXPLICIT LABEL NEAR THE DATE**
""",
                statement_date.render(),
            )

        meters = root["meters"]
        self.assertIsInstance(meters, Group)

        pmp = meters.prompt
        self.assertIsNotNone(pmp)
        if pmp:
            self.assertEqual(pmp.attr_name, "meters")
        self.assertEqual(
            """
# meters Definition

A meter is a total measurement of a utility service, charged by a utility provider, over some service period (a time period with a beginning and end).
""",
            meters.render(),
        )

        self.assertIn("meter_number", meters.fields)
        mn = meters.fields["meter_number"]
        self.assertIsInstance(mn, ExtractedField)

        if isinstance(mn, ExtractedField):
            pmp = mn.prompt
            self.assertIsNotNone(pmp)
            if pmp:
                self.assertEqual(pmp.attr_name, "meter_number")
            self.assertEqual(
                """
## meter_number

Field:                  meter_number
Description:            unique identifier for the meter that made the utility service measurement
Format:                 unique string, **always** formatted as a string
Example Identifiers:    Meter #, Meter ID, Premises Number
Special Instructions:
You must follow the following process to determine if you have found a valid meter number:
""",
                mn.render(),
            )

        self.assertIn("service_address", meters.fields)
        sa = meters.fields["service_address"]
        self.assertIsInstance(sa, ExtractedField)

        if isinstance(sa, ExtractedField):
            pmp = sa.prompt
            self.assertIsNotNone(pmp)
            if pmp:
                self.assertEqual(pmp.attr_name, "service_address")
            self.assertEqual(
                """
## service_address

Field:                  service_address
Default Value:          test address
Format:                 string
Example Identifiers:    Premises Identifier, Premises Descriptor
Special Instructions:
- Strip the recipient name from the service address if it is a proper name, such as a person or company or municipality
""",
                sa.render(),
            )

    def test_get_prompt_1(self) -> None:
        tsts: typing.List[typing.Dict[str, typing.Any]] = [
            {
                "expect": Prompt(
                    attr_name="meters",
                    instructions="A meter is a total measurement of a utility service, charged by a utility provider, over some service period (a time period with a beginning and end).\n",
                ),
                "name": "meters",
                "yaml": SAMPLE_YAML_1,
            },
            {
                "expect": Exception(
                    "[latest] [latest.yaml] is missing a [meter] entry"
                ),
                "name": "meter",
                "yaml": SAMPLE_YAML_1,
            },
            {
                "expect": Prompt(attr_name="meters", instructions="## meters\n"),
                "name": "statement.meters",
                "yaml": SAMPLE_YAML_2,
            },
            {
                "expect": Exception(
                    "[latest] [latest.yaml] is missing a [meter] entry at [statement.meter]"
                ),
                "name": "statement.meter",
                "yaml": SAMPLE_YAML_2,
            },
            {
                "expect": Prompt(
                    attr_name="statement_date",
                    identifiers=["Statement Date"],
                    instructions="## statement_date\n",
                    description="date when the invoice was computed or sent to the customer",
                    type="str",
                ),
                "name": "statement.statement_date",
                "yaml": SAMPLE_YAML_2,
            },
            {
                "expect": Exception(
                    "[latest] [latest.yaml] entry at [statement.statement_date] is not a group"
                ),
                "name": "statement.statement_date.meters",
                "yaml": SAMPLE_YAML_2,
            },
            {
                "expect": Prompt(
                    attr_name="meter_number",
                    identifiers=["Meter Number"],
                    instructions="## meter_number\n",
                    description="unique identifier for the meter that made the utility service measurement",
                    type="str",
                ),
                "name": "statement.meters.meter_number",
                "yaml": SAMPLE_YAML_2,
            },
            {
                "expect": Exception(
                    "[latest] [latest.yaml] is missing a [meter] entry at [statement.meters.meter]"
                ),
                "name": "statement.meters.meter",
                "yaml": SAMPLE_YAML_2,
            },
        ]

        for idx, tst in enumerate(tsts):
            source = TestSource(tst["yaml"])
            manager = PromptManager(cache_source=source, config_source=source)

            if isinstance(tst["expect"], Exception):
                with self.assertRaises(Exception) as e:
                    manager.get_prompt(tst["name"])
                self.assertEqual(str(e.exception), str(tst["expect"]))
            else:
                pmp = manager.get_prompt(tst["name"])
                self.assertEqual(pmp, tst["expect"], f"\n\n[{idx}]\n\n")

    def test_reload_if_changed_1(self) -> None:
        source = TestSource(SAMPLE_YAML_1)
        manager = PromptManager(cache_source=source, config_source=source)
        root = manager.get_fields_for_workflow("latest")

        self.assertIn("statement", root)
        self.assertIsInstance(root["statement"], Group)

        self.assertIn("statement_date", root["statement"].fields)
        self.assertEqual(len(root["statement"].fields), 1)
        statement_date = root["statement"].fields["statement_date"]
        self.assertIsInstance(statement_date, ExtractedField)

        if isinstance(statement_date, ExtractedField):
            pmp = statement_date.prompt
            self.assertIsNotNone(pmp)
            if pmp:
                self.assertEqual(pmp.attr_name, "statement_date")
            self.assertEqual(
                """
## statement_date

Field:                  statement_date
Description:            date when the invoice was computed or sent to the customer
Format:                 YYYY-mm-dd date string
Example Identifiers:    Invoice Date, Billing Date, Account Summary as of XX/XX/XXXX, Bill Date, Account Balance as of XX/XX/XXXX
Special Instructions:
- **DO NOT INCLUDE THIS VALUE IF YOU CANNOT FIND AN EXPLICIT LABEL NEAR THE DATE**
""",
                statement_date.render(),
            )

        updated_yaml = SAMPLE_YAML_1.replace(
            "- **DO NOT INCLUDE THIS VALUE IF YOU CANNOT FIND AN EXPLICIT LABEL NEAR THE DATE**",
            "## updated_statement_date",
        )
        source.update(updated_yaml, "v2")

        manager.reload_if_changed()
        updated_fields = manager.get_fields_for_workflow(workflow_id="v2")

        self.assertIn("statement", updated_fields)
        self.assertEqual(len(updated_fields["statement"].fields), 1)

        self.assertIn("statement_date", updated_fields["statement"].fields)
        statement_date = updated_fields["statement"].fields["statement_date"]
        self.assertIsInstance(statement_date, ExtractedField)

        if isinstance(statement_date, ExtractedField):
            pmp = statement_date.prompt
            self.assertIsNotNone(pmp)
            if pmp:
                self.assertEqual(pmp.attr_name, "statement_date")
            self.assertEqual(
                """
## statement_date

Field:                  statement_date
Description:            date when the invoice was computed or sent to the customer
Format:                 YYYY-mm-dd date string
Example Identifiers:    Invoice Date, Billing Date, Account Summary as of XX/XX/XXXX, Bill Date, Account Balance as of XX/XX/XXXX
Special Instructions:
## updated_statement_date
""",
                statement_date.render(),
                f"\n\n{statement_date.render()}\n\n",
            )

    def test_workflow_extract_dict(self):
        source = TestSource(SAMPLE_YAML_1)
        manager = PromptManager(cache_source=source, config_source=source)

        js = json.dumps(manager.workflow_extract_dict(), indent=2)
        ym = json.dumps(yaml.safe_load(SAMPLE_YAML_1), indent=2)

        self.maxDiff = None
        self.assertEqual(js, ym)


def check_value(
    key: str, mn: TestPromptManager, pmp: Prompt, expect: typing.Dict[str, typing.Any]
):
    if key in expect:
        mn.assertEqual(pmp.__getattribute__(key), expect[key])
    else:
        mn.assertIsNone(pmp.__getattribute__(key))

    if key == "attr_name":
        mn.assertEqual(pmp.key(), expect[key])


def check_prompt(
    mn: TestPromptManager,
    pmp: typing.Optional[Prompt],
    expect: typing.Dict[str, typing.Any],
):
    mn.assertIsNotNone(pmp)
    if pmp:
        check_value("attr_name", mn, pmp, expect)
        check_value("default", mn, pmp, expect)
        check_value("description", mn, pmp, expect)
        check_value("format", mn, pmp, expect)
        check_value("identifiers", mn, pmp, expect)
        check_value("instructions", mn, pmp, expect)
        check_value("required", mn, pmp, expect)
        check_value("type", mn, pmp, expect)
