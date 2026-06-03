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

SAMPLE_YAML_PSEUDO_GROUPS = """
statement:
  prompt:
    instructions: Extract statement-level fields for the final statement object.
  fields:
    account_number:
      prompt:
        description: The account number printed on the statement.
        identifiers:
          - Account Number
          - Account #
        instructions: Return the account number exactly as printed.
        type: str
    bill_start_date:
      prompt:
        description: The billing period start date.
        identifiers:
          - Billing Period
          - Service From
        instructions: Return the billing period start date as YYYY-MM-DD.
        type: str
    total_amount_due:
      prompt:
        description: The total amount due.
        identifiers:
          - Total Amount Due
          - Amount Due
        instructions: Return the total amount due as a number.
        type: float
    late_fee:
      prompt:
        description: The late fee charged on this statement.
        identifiers:
          - Late Fee
        instructions: Return the late fee as a number.
        type: float

customer:
  fields:
    customer_name:
      prompt:
        description: The customer name as printed.
        identifiers:
          - Customer Name
          - Name
        instructions: Return the customer name exactly as printed.
        type: str

service_address:
  fields:
    street:
      prompt:
        description: The service street address.
        identifiers:
          - Service Address
        instructions: Return the street address exactly as printed.
        type: str

_pseudo_groups:
  statement_identity:
    fields:
      account_number:
        path: statement.account_number
      bill_start_date:
        path: statement.bill_start_date

  statement_totals:
    prompt:
      instructions: Extract only the statement total fields.
    fields:
      total_amount_due:
        path: statement.total_amount_due

  customer_packet:
    prompt:
      instructions: Extract customer and service-address fields together.
    fields:
      customer_name:
        path: customer.customer_name
      service_street:
        path: service_address.street
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
