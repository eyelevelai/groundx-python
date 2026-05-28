"""Cross-test fixtures used by tests/extract/prompt/test_manager.py
and tests/extract/classes/test_document.py.

Underscore prefix keeps pytest from collecting this as a test module.
TestSource is named with a Test prefix because it subclasses Source as a
testing-double, but pytest warns when it tries to collect it as a test
class; hiding it in an underscore-prefixed module sidesteps that.
"""

import typing

from groundx.extract.prompt.source import Source


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
    __test__ = False  # not a unittest class — Source subclass used as testing fixture

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
