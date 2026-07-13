import json
import types
import typing
import unittest

import yaml
from ._fixtures import (
    SAMPLE_YAML_1,
    SAMPLE_YAML_2,
    SAMPLE_YAML_PSEUDO_GROUPS,
    TestSource,
)

from groundx.extract import FinalFieldPath, PreparedExtractionYaml, prepare_extraction_yaml
from groundx.extract.classes.field import ExtractedField
from groundx.extract.classes.group import Group
from groundx.extract.classes.prompt import Prompt
from groundx.extract.prompt.manager import PromptManager, load_from_yaml


class FailingSource(TestSource):
    def __init__(self) -> None:
        super().__init__("")

    def fetch(self, workflow_id: str) -> typing.Tuple[str, str]:
        raise Exception(f"missing prompt yaml [{workflow_id}]")

    def peek(self, workflow_id: str) -> typing.Optional[str]:
        return None


class FlakyCachedSource(TestSource):
    def __init__(self, raw: str) -> None:
        super().__init__(raw)
        self.fetch_calls = 0
        self.peek_calls = 0
        self.fail_fetch = False
        self.fail_peek = False

    def fetch(self, workflow_id: str) -> typing.Tuple[str, str]:
        self.fetch_calls += 1
        if self.fail_fetch:
            raise Exception(f"fetch unavailable [{workflow_id}]")
        return super().fetch(workflow_id)

    def peek(self, workflow_id: str) -> typing.Optional[str]:
        self.peek_calls += 1
        if self.fail_peek:
            raise Exception(f"peek unavailable [{workflow_id}]")
        return super().peek(workflow_id)


CUSTOM_WORKFLOW_YAML = """
extraction_policy_version: v1

workflow:
  template:
    BILLING_HINT: Prefer values from the charge table.
  custom_steps:
    - name: line_item_labels
      level: chunk
      kind: keys
      required_template_keys:
        - BILLING_HINT
      config:
        all:
          includes:
            text: true

line_items:
  workflow_step: line_item_labels
  fields:
    description:
      workflow_output_key: label
      prompt:
        identifiers:
          - Description
        instructions: Return the printed line-item description.
        type: str
"""


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

    def test_cache_workflow_falls_back_to_workflow_api_extract(self) -> None:
        workflow_extract: typing.Dict[str, typing.Any] = {
            "statement_identity": {
                "fields": {
                    "provider_name": {
                        "prompt": {
                            "description": "Provider name.",
                            "instructions": "Return the provider name.",
                            "type": "str",
                        }
                    }
                }
            },
            "_groundx_persisted_extract": {
                "extraction_policy_version": "v1",
                "statement": {
                    "workflow_step": "chunk-instruct",
                    "fields": {
                        "provider_name": {
                            "prompt": {
                                "description": "Provider name.",
                                "instructions": "Return the provider name.",
                                "type": "str",
                            }
                        }
                    },
                },
                "_pseudo_groups": {
                    "statement_identity": {
                        "workflow_step": "chunk-instruct",
                        "fields": {
                            "provider_name": {
                                "path": "/statement/provider_name",
                            }
                        },
                    }
                },
            },
        }

        class Workflows:
            def __init__(self) -> None:
                self.requested_ids: typing.List[str] = []

            def get(self, id: str) -> typing.Any:
                self.requested_ids.append(id)
                return types.SimpleNamespace(
                    workflow=types.SimpleNamespace(
                        workflow_id=id,
                        extract=workflow_extract,
                    )
                )

        workflows = Workflows()
        gx_client = types.SimpleNamespace(workflows=workflows)
        source = FailingSource()
        manager = PromptManager(
            cache_source=source,
            config_source=source,
            gx_client=typing.cast(typing.Any, gx_client),
            default_file_name="wf-1",
            default_workflow_id="wf-1",
            top_level_metadata_keys={"extraction_policy_version"},
            workflow_group_metadata_keys={"workflow_step"},
        )

        fields = manager.get_fields_for_workflow(workflow_id="wf-1")

        self.assertIn("wf-1", workflows.requested_ids)
        self.assertIn("statement_identity", fields)
        self.assertEqual(
            manager.top_level_metadata(workflow_id="wf-1"),
            {"extraction_policy_version": "v1"},
        )
        self.assertEqual(
            manager.workflow_field_paths(workflow_id="wf-1"),
            {"statement_identity": {"provider_name": "/statement/provider_name"}},
        )
        persisted = manager.persisted_workflow_extract_dict(workflow_id="wf-1")
        self.assertEqual(
            persisted["_groundx_persisted_extract"],
            workflow_extract["_groundx_persisted_extract"],
        )
        self.assertEqual(
            persisted["statement_identity"]["fields"]["provider_name"]["prompt"][
                "attr_name"
            ],
            "provider_name",
        )

    def test_reload_if_changed_falls_back_to_workflow_api_extract(self) -> None:
        workflow_extract: typing.Dict[str, typing.Any] = {
            "statement_identity": {
                "fields": {
                    "provider_name": {
                        "prompt": {
                            "description": "Provider name.",
                            "instructions": "Return the provider name.",
                            "type": "str",
                        }
                    }
                }
            },
            "_groundx_persisted_extract": {
                "extraction_policy_version": "v1",
                "statement": {
                    "fields": {
                        "provider_name": {
                            "prompt": {
                                "description": "Provider name.",
                                "instructions": "Return the provider name.",
                                "type": "str",
                            }
                        }
                    },
                },
                "_pseudo_groups": {
                    "statement_identity": {
                        "fields": {
                            "provider_name": {
                                "path": "/statement/provider_name",
                            }
                        },
                    }
                },
            },
        }

        class Workflows:
            def __init__(self) -> None:
                self.requested_ids: typing.List[str] = []

            def get(self, id: str) -> typing.Any:
                self.requested_ids.append(id)
                return types.SimpleNamespace(
                    workflow=types.SimpleNamespace(
                        workflow_id=id,
                        extract=workflow_extract,
                    )
                )

        workflows = Workflows()
        gx_client = types.SimpleNamespace(workflows=workflows)
        source = FailingSource()
        manager = PromptManager(
            cache_source=source,
            config_source=source,
            gx_client=typing.cast(typing.Any, gx_client),
            default_file_name="wf-1",
            default_workflow_id="wf-1",
            top_level_metadata_keys={"extraction_policy_version"},
        )

        workflow_extract["statement_identity"]["fields"]["provider_name"]["prompt"][
            "instructions"
        ] = "Return the updated provider name."
        workflow_extract["_groundx_persisted_extract"]["statement"]["fields"][
            "provider_name"
        ]["prompt"]["instructions"] = "Return the updated provider name."

        manager.reload_if_changed("wf-1")

        self.assertGreaterEqual(workflows.requested_ids.count("wf-1"), 2)
        self.assertEqual(
            manager.top_level_metadata(workflow_id="wf-1"),
            {"extraction_policy_version": "v1"},
        )
        provider = manager.group_field(
            "statement_identity",
            "provider_name",
            workflow_id="wf-1",
        )
        assert provider is not None
        assert provider.prompt is not None
        self.assertEqual(
            provider.prompt.instructions,
            "Return the updated provider name.",
        )

    def test_cached_workflow_survives_source_peek_failure(self) -> None:
        source = FlakyCachedSource(SAMPLE_YAML_1)
        manager = PromptManager(cache_source=source, config_source=source)
        self.assertEqual(source.fetch_calls, 1)

        source.fail_peek = True
        source.fail_fetch = True

        fields = manager.get_fields_for_workflow()

        self.assertIn("statement", fields)
        self.assertEqual(source.fetch_calls, 1)

    def test_reload_if_changed_keeps_cache_when_source_peek_fails(self) -> None:
        source = FlakyCachedSource(SAMPLE_YAML_1)
        manager = PromptManager(cache_source=source, config_source=source)
        self.assertEqual(source.fetch_calls, 1)

        source.fail_peek = True
        source.fail_fetch = True

        manager.reload_if_changed()
        fields = manager.get_fields_for_workflow()

        self.assertIn("statement", fields)
        self.assertEqual(source.fetch_calls, 1)

    def test_prepare_extraction_yaml_with_pseudo_groups(self) -> None:
        prepared = prepare_extraction_yaml(SAMPLE_YAML_PSEUDO_GROUPS)

        self.assertIsInstance(prepared, PreparedExtractionYaml)
        self.assertEqual(
            list(prepared.groups.keys()),
            ["statement", "customer", "service_address"],
        )
        self.assertEqual(
            list(prepared.pseudo_groups.keys()),
            ["statement_identity", "statement_totals", "customer_packet"],
        )
        self.assertEqual(
            list(prepared.workflow_groups.keys()),
            [
                "statement_identity",
                "statement_totals",
                "customer_packet",
                "statement",
            ],
        )
        self.assertEqual(
            prepared.workflow_field_paths,
            {
                "statement_identity": {
                    "account_number": "/statement/account_number",
                    "bill_start_date": "/statement/bill_start_date",
                },
                "statement_totals": {
                    "total_amount_due": "/statement/total_amount_due",
                },
                "customer_packet": {
                    "customer_name": "/customer/customer_name",
                    "service_street": "/service_address/street",
                },
                "statement": {
                    "late_fee": "/statement/late_fee",
                },
            },
        )

        statement_identity = prepared.workflow_groups["statement_identity"]
        self.assertEqual(
            statement_identity["prompt"]["instructions"],
            "Extract statement-level fields for the final statement object.",
        )
        self.assertEqual(
            statement_identity["fields"]["account_number"]["prompt"]["attr_name"],
            "account_number",
        )

    def test_load_from_yaml_returns_final_groups_only_with_pseudo_groups(self) -> None:
        root = load_from_yaml(SAMPLE_YAML_PSEUDO_GROUPS)

        self.assertEqual(list(root.keys()), ["statement", "customer", "service_address"])
        self.assertIn("total_amount_due", root["statement"].fields)
        self.assertIn("customer_name", root["customer"].fields)
        self.assertNotIn("_pseudo_groups", root)
        self.assertNotIn("statement_identity", root)

    def test_manager_workflow_groups_use_pseudo_group_names(self) -> None:
        source = TestSource(SAMPLE_YAML_PSEUDO_GROUPS)
        manager = PromptManager(cache_source=source, config_source=source)

        workflow = manager.get_fields_for_workflow("latest")

        self.assertEqual(
            list(workflow.keys()),
            [
                "statement_identity",
                "statement_totals",
                "customer_packet",
                "statement",
            ],
        )

        statement_identity = workflow["statement_identity"]
        self.assertIsInstance(statement_identity, Group)
        self.assertIsNotNone(statement_identity.prompt)
        if statement_identity.prompt:
            self.assertEqual(statement_identity.prompt.attr_name, "statement_identity")
            self.assertEqual(
                statement_identity.prompt.instructions,
                "Extract statement-level fields for the final statement object.",
            )
        self.assertEqual(
            list(statement_identity.fields.keys()),
            ["account_number", "bill_start_date"],
        )

        customer_packet = workflow["customer_packet"]
        service_street = customer_packet.fields["service_street"]
        self.assertIsInstance(service_street, ExtractedField)
        if isinstance(service_street, ExtractedField):
            self.assertIsNotNone(service_street.prompt)
            if service_street.prompt:
                self.assertEqual(service_street.prompt.attr_name, "service_street")
                self.assertEqual(
                    service_street.prompt.description,
                    "The service street address.",
                )

        residual_statement = workflow["statement"]
        self.assertEqual(list(residual_statement.fields.keys()), ["late_fee"])

    def test_manager_data_object_groups_remain_final_shape(self) -> None:
        source = TestSource(SAMPLE_YAML_PSEUDO_GROUPS)
        manager = PromptManager(cache_source=source, config_source=source)

        data_groups = manager.get_fields_for_data_object("latest")

        self.assertEqual(
            list(data_groups.keys()), ["statement", "customer", "service_address"]
        )
        self.assertEqual(
            list(data_groups["statement"].fields.keys()),
            ["account_number", "bill_start_date", "total_amount_due", "late_fee"],
        )

    def test_manager_workflow_field_paths(self) -> None:
        source = TestSource(SAMPLE_YAML_PSEUDO_GROUPS)
        manager = PromptManager(cache_source=source, config_source=source)

        self.assertEqual(
            manager.workflow_field_paths(),
            {
                "statement_identity": {
                    "account_number": "/statement/account_number",
                    "bill_start_date": "/statement/bill_start_date",
                },
                "statement_totals": {
                    "total_amount_due": "/statement/total_amount_due",
                },
                "customer_packet": {
                    "customer_name": "/customer/customer_name",
                    "service_street": "/service_address/street",
                },
                "statement": {
                    "late_fee": "/statement/late_fee",
                },
            },
        )

    def test_manager_exposes_prepared_metadata_surfaces(self) -> None:
        raw = """
extraction_policy_version: v1

statement:
  workflow_step: chunk-instruct
  unique_attrs:
    - account_number
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    fields:
      account_number:
        path: /statement/account_number
"""
        source = TestSource(raw)
        manager = PromptManager(
            cache_source=source,
            config_source=source,
            final_group_metadata_keys={"unique_attrs"},
            workflow_group_metadata_keys={"workflow_step"},
        )

        self.assertEqual(manager.top_level_metadata(), {"extraction_policy_version": "v1"})
        self.assertEqual(
            manager.final_group_metadata(),
            {"statement": {"unique_attrs": ["account_number"]}},
        )
        self.assertEqual(
            manager.workflow_group_metadata(),
            {"statement_identity": {"workflow_step": "chunk-instruct"}},
        )

    def test_prepare_extraction_yaml_rejects_unsupported_top_level_scalar_metadata(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
unsupported_policy_version: v1
statement:
  fields:
    account_number:
      prompt:
        instructions: Return the account number.
        type: str
"""
            )

        message = str(exc.exception)
        self.assertIn("unsupported top-level metadata [unsupported_policy_version]", message)
        self.assertIn("workflow metadata", message)

    def test_prepare_extraction_yaml_accepts_supported_policy_version_metadata(
        self,
    ) -> None:
        prepared = prepare_extraction_yaml(
            """
extraction_policy_version: v1
statement:
  final_value_aliases:
    account_number: account_number
  fields:
    account_number:
      prompt:
        instructions: Return the account number.
        type: str
"""
        )

        self.assertEqual(
            prepared.top_level_metadata,
            {"extraction_policy_version": "v1"},
        )
        self.assertIn("statement", prepared.groups)

    def test_prepare_extraction_yaml_identity_route_map_for_legacy_yaml(self) -> None:
        prepared = prepare_extraction_yaml(SAMPLE_YAML_1)

        self.assertEqual(list(prepared.groups.keys()), ["statement", "meters"])
        self.assertEqual(list(prepared.workflow_groups.keys()), ["statement", "meters"])
        self.assertEqual(
            prepared.workflow_field_paths,
            {
                "statement": {
                    "statement_date": "/statement/statement_date",
                },
                "meters": {
                    "meter_number": "/meters/meter_number",
                    "service_address": "/meters/service_address",
                },
            },
        )

    def test_prepare_extraction_yaml_rejects_duplicate_keys(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
statement:
  fields: {}
statement:
  fields: {}
"""
            )

        self.assertIn("duplicate YAML key", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_duplicate_pseudo_routes(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  first:
    fields:
      account_number:
        path: /statement/account_number
  second:
    fields:
      duplicate_account_number:
        path: /statement/account_number
"""
            )

        self.assertIn("routed more than once", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_unknown_pseudo_path(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  identity:
    fields:
      missing:
        path: /statement/missing
"""
            )

        self.assertIn("unknown final field path", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_malformed_pseudo_field_mapping(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    fields:
      account_number: /statement/account_number
"""
            )

        self.assertIn(
            "_pseudo_groups.statement_identity.fields.account_number",
            str(exc.exception),
        )

    def test_prepare_extraction_yaml_rejects_pseudo_final_group_name_collision(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement:
    fields:
      account_number:
        path: /statement/account_number
"""
            )

        self.assertIn("collides with a final group", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_pseudo_group_include(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

_defs:
  identity_fields:
    fields:
      account_number:
        prompt:
          identifiers:
            - Account Number
          instructions: Return the account number.
          type: str
statement:
  include: identity_fields
  fields: {}
_pseudo_groups:
  statement_identity:
    include: identity_fields
    fields:
      account_number:
        path: /statement/account_number
"""
            )

        self.assertIn("unsupported pseudo-group keys", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_scalar_prompt_shorthand(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
statement:
  prompt: Extract statement fields.
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
"""
            )

        self.assertIn("mapping-shaped prompt", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_multi_parent_pseudo_without_prompt(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

customer:
  fields:
    customer_name:
      prompt:
        identifiers:
          - Customer Name
        instructions: Return the customer name.
        type: str
service_address:
  fields:
    street:
      prompt:
        identifiers:
          - Service Address
        instructions: Return the service address.
        type: str
_pseudo_groups:
  customer_packet:
    fields:
      customer_name:
        path: /customer/customer_name
      service_street:
        path: /service_address/street
"""
            )

        self.assertIn("must declare prompt", str(exc.exception))

    def test_prepare_extraction_yaml_composes_defs_fields_only(self) -> None:
        prepared = prepare_extraction_yaml(
            """
extraction_policy_version: v1

_defs:
  identity_fields:
    fields:
      account_number:
        prompt:
          identifiers:
            - Account Number
          instructions: Return the account number.
          type: str
statement:
  include:
    - identity_fields
  fields:
    total_amount_due:
      prompt:
        identifiers:
          - Total Amount Due
        instructions: Return the total amount due.
        type: float
_pseudo_groups:
  statement_identity:
    fields:
      account_number:
        path: /statement/account_number
"""
        )

        self.assertEqual(
            list(prepared.groups["statement"]["fields"].keys()),
            ["account_number", "total_amount_due"],
        )
        self.assertEqual(
            prepared.workflow_field_paths,
            {
                "statement_identity": {
                    "account_number": "/statement/account_number",
                },
                "statement": {
                    "total_amount_due": "/statement/total_amount_due",
                },
            },
        )

    def test_final_field_path_parses_json_pointer_routes(self) -> None:
        parsed = FinalFieldPath.parse("/statement/account~1number")

        self.assertEqual(parsed.segments, ("statement", "account/number"))
        self.assertEqual(parsed.to_pointer(), "/statement/account~1number")
        self.assertEqual(str(parsed), "/statement/account~1number")

        dotted = FinalFieldPath.parse("/statement/account.number")
        self.assertEqual(dotted.segments, ("statement", "account.number"))

    def test_final_field_path_rejects_malformed_or_unsupported_paths(self) -> None:
        for pointer in (
            "statement.account_number",
            "/statement",
            "/statement/account/extra",
            "/statement/account~2number",
            "/statement/account~",
        ):
            with self.subTest(pointer=pointer):
                with self.assertRaises(ValueError):
                    FinalFieldPath.parse(pointer)

    def test_prepare_extraction_yaml_separates_metadata_surfaces(self) -> None:
        prepared = prepare_extraction_yaml(
            """
extraction_policy_version: v1

statement:
  workflow_step: chunk-instruct
  unique_attrs:
    - account_number
  final_value_aliases:
    account_number: account_number
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
    total_amount_due:
      prompt:
        identifiers:
          - Total Amount Due
        instructions: Return the total amount due.
        type: float
_pseudo_groups:
  statement_identity:
    fields:
      account_number:
        path: /statement/account_number
  statement_totals:
    workflow_step: chunk-keys
    fields:
      total_amount_due:
        path: /statement/total_amount_due
""",
            final_group_metadata_keys={"unique_attrs", "final_value_aliases"},
            workflow_group_metadata_keys={"workflow_step"},
        )

        self.assertEqual(
            prepared.top_level_metadata,
            {"extraction_policy_version": "v1"},
        )
        self.assertEqual(
            prepared.final_group_metadata,
            {
                "statement": {
                    "unique_attrs": ["account_number"],
                    "final_value_aliases": {"account_number": "account_number"},
                }
            },
        )
        self.assertEqual(
            prepared.workflow_group_metadata,
            {
                "statement_identity": {"workflow_step": "chunk-instruct"},
                "statement_totals": {"workflow_step": "chunk-keys"},
            },
        )
        self.assertNotIn("workflow_step", prepared.groups["statement"])
        self.assertNotIn("unique_attrs", prepared.workflow_groups["statement_identity"])
        self.assertFalse(hasattr(prepared, "pseudo_group_metadata"))

    def test_prepare_extraction_yaml_resolves_workflow_step_positive_cases(self) -> None:
        prepared = prepare_extraction_yaml(
            """
extraction_policy_version: v1

statement:
  workflow_step: chunk-instruct
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
    total_amount_due:
      prompt:
        identifiers:
          - Total Amount Due
        instructions: Return the total amount due.
        type: float
customer:
  workflow_step: chunk-summary
  fields:
    customer_name:
      prompt:
        identifiers:
          - Customer Name
        instructions: Return the customer name.
        type: str
service_address:
  workflow_step: chunk-summary
  fields:
    street:
      prompt:
        identifiers:
          - Service Address
        instructions: Return the street.
        type: str
notes:
  fields:
    memo:
      prompt:
        identifiers:
          - Memo
        instructions: Return the memo.
        type: str
_pseudo_groups:
  statement_identity:
    fields:
      account_number:
        path: /statement/account_number
  statement_totals:
    workflow_step: chunk-keys
    fields:
      total_amount_due:
        path: /statement/total_amount_due
  customer_packet:
    prompt:
      instructions: Extract customer details.
    fields:
      customer_name:
        path: /customer/customer_name
      service_street:
        path: /service_address/street
""",
            workflow_group_metadata_keys={"workflow_step"},
        )

        self.assertEqual(
            prepared.workflow_group_metadata,
            {
                "statement_identity": {"workflow_step": "chunk-instruct"},
                "statement_totals": {"workflow_step": "chunk-keys"},
                "customer_packet": {"workflow_step": "chunk-summary"},
            },
        )

    def test_prepare_extraction_yaml_rejects_ambiguous_workflow_step_inheritance(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

customer:
  workflow_step: chunk-instruct
  fields:
    customer_name:
      prompt:
        identifiers:
          - Customer Name
        instructions: Return the customer name.
        type: str
service_address:
  workflow_step: chunk-summary
  fields:
    street:
      prompt:
        identifiers:
          - Service Address
        instructions: Return the street.
        type: str
_pseudo_groups:
  customer_packet:
    prompt:
      instructions: Extract customer details.
    fields:
      customer_name:
        path: /customer/customer_name
      service_street:
        path: /service_address/street
""",
                workflow_group_metadata_keys={"workflow_step"},
            )

        self.assertIn("explicit [workflow_step] is required", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_partially_missing_workflow_step_inheritance(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

customer:
  workflow_step: chunk-instruct
  fields:
    customer_name:
      prompt:
        identifiers:
          - Customer Name
        instructions: Return the customer name.
        type: str
service_address:
  fields:
    street:
      prompt:
        identifiers:
          - Service Address
        instructions: Return the street.
        type: str
_pseudo_groups:
  customer_packet:
    prompt:
      instructions: Extract customer details.
    fields:
      customer_name:
        path: /customer/customer_name
      service_street:
        path: /service_address/street
""",
                workflow_group_metadata_keys={"workflow_step"},
            )

        self.assertIn("explicit [workflow_step] is required", str(exc.exception))

    def test_prepare_extraction_yaml_preserves_ordinary_aliases_by_deep_copy(
        self,
    ) -> None:
        prepared = prepare_extraction_yaml(
            """
statement:
  fields:
    account_number:
      prompt: &account_prompt
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
    alternate_account_number:
      prompt: *account_prompt
"""
        )

        account_prompt = prepared.groups["statement"]["fields"]["account_number"]["prompt"]
        alternate_prompt = prepared.groups["statement"]["fields"][
            "alternate_account_number"
        ]["prompt"]

        self.assertEqual(account_prompt, alternate_prompt)
        self.assertIsNot(account_prompt, alternate_prompt)

    def test_prepare_extraction_yaml_rejects_yaml_merge_keys(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
base: &base
  fields: {}
statement:
  <<: *base
"""
            )

        self.assertIn("YAML merge keys", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_recursive_aliases(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
statement: &statement
  fields:
    self: *statement
"""
            )

        self.assertIn("cyclic YAML", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_empty_pseudo_group_fields(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    fields: {}
"""
            )

        self.assertIn("empty fields", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_unsupported_pseudo_group_metadata(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    owner: billing
    fields:
      account_number:
        path: /statement/account_number
"""
            )

        self.assertIn("unsupported pseudo-group keys", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_defs_prompt_text(self) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
_defs:
  identity_fields:
    prompt:
      instructions: Shared prompt text is not allowed in defs.
    fields: {}
statement:
  include: identity_fields
  fields: {}
"""
            )

        self.assertIn("unsupported _defs keys", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_duplicate_nested_prompt_key(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
        type: int
"""
            )

        self.assertIn("duplicate YAML key [type]", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_duplicate_pseudo_group_names(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    fields:
      account_number:
        path: /statement/account_number
  statement_identity:
    fields:
      duplicate_account_number:
        path: /statement/account_number
"""
            )

        self.assertIn("duplicate YAML key [statement_identity]", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_duplicate_pseudo_field_keys(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

statement:
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    fields:
      account_number:
        path: /statement/account_number
      account_number:
        path: /statement/account_number
"""
            )

        self.assertIn("duplicate YAML key [account_number]", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_duplicate_defs_fragment_names(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
_defs:
  identity_fields:
    fields: {}
  identity_fields:
    fields: {}
statement:
  include: identity_fields
  fields: {}
"""
            )

        self.assertIn("duplicate YAML key [identity_fields]", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_duplicate_final_field_from_defs(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
_defs:
  identity_fields:
    fields:
      account_number:
        prompt:
          identifiers:
            - Account Number
          instructions: Return the account number.
          type: str
statement:
  include: identity_fields
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number again.
        type: str
"""
            )

        self.assertIn(
            "duplicate final field name [statement.account_number]",
            str(exc.exception),
        )

    def test_prepare_extraction_yaml_treats_pseudo_workflow_step_null_as_unset(
        self,
    ) -> None:
        prepared = prepare_extraction_yaml(
            """
extraction_policy_version: v1

statement:
  workflow_step: chunk-instruct
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    workflow_step:
    fields:
      account_number:
        path: /statement/account_number
""",
            workflow_group_metadata_keys={"workflow_step"},
        )

        self.assertEqual(
            prepared.workflow_group_metadata,
            {"statement_identity": {"workflow_step": "chunk-instruct"}},
        )

    def test_prepare_extraction_yaml_preserves_empty_string_workflow_step(
        self,
    ) -> None:
        prepared = prepare_extraction_yaml(
            """
extraction_policy_version: v1

statement:
  workflow_step: chunk-instruct
  fields:
    account_number:
      prompt:
        identifiers:
          - Account Number
        instructions: Return the account number.
        type: str
_pseudo_groups:
  statement_identity:
    workflow_step: ""
    fields:
      account_number:
        path: /statement/account_number
""",
            workflow_group_metadata_keys={"workflow_step"},
        )

        self.assertEqual(
            prepared.workflow_group_metadata,
            {"statement_identity": {"workflow_step": ""}},
        )

    def test_prepare_extraction_yaml_accepts_custom_workflow_steps(self) -> None:
        prepared = prepare_extraction_yaml(CUSTOM_WORKFLOW_YAML)

        self.assertNotIn("workflow", prepared.groups)
        self.assertNotIn("workflow", prepared.workflow_groups)
        self.assertIn("line_items", prepared.groups)
        self.assertIn("description", prepared.groups["line_items"]["fields"])
        self.assertNotIn("workflow_step", prepared.groups["line_items"])
        self.assertNotIn(
            "workflow_output_key",
            prepared.groups["line_items"]["fields"]["description"],
        )

        workflow = prepared.persisted_workflow_extract["workflow"]
        self.assertEqual(workflow["metadata_version"], 1)
        self.assertEqual(
            workflow["template"],
            {"BILLING_HINT": "Prefer values from the charge table."},
        )
        self.assertEqual(
            workflow["custom_steps"],
            [
                {
                    "name": "line_item_labels",
                    "level": "chunk",
                    "kind": "keys",
                    "required_template_keys": ["BILLING_HINT"],
                    "config": {
                        "all": {
                            "includes": {"text": True},
                        }
                    },
                }
            ],
        )
        self.assertEqual(
            workflow["output_routes"],
            [
                {
                    "workflow_group": "line_items",
                    "workflow_field": "description",
                    "final_path": "/line_items/description",
                    "step_name": "line_item_labels",
                    "level": "chunk",
                    "output_map": "customChunkOutputs",
                    "output_key": "label",
                    "readback_path": (
                        "/chunks/*/customChunkOutputs/line_item_labels/label"
                    ),
                }
            ],
        )
        self.assertEqual(
            workflow["leaf_fields"],
            [
                {
                    "final_path": "/line_items/description",
                    "workflow_group": "line_items",
                    "workflow_field": "description",
                    "step_name": "line_item_labels",
                    "level": "chunk",
                    "output_key": "label",
                    "field_type": "str",
                    "is_repeated": False,
                    "repetition_scope": "none",
                }
            ],
        )
        self.assertEqual(workflow["field_counts"], {"line_item_labels": 1})
        self.assertRegex(workflow["schema_hash"], r"^[0-9a-f]{64}$")

    def test_prepare_extraction_yaml_routes_repeated_custom_fields_with_list_name(
        self,
    ) -> None:
        prepared = prepare_extraction_yaml(
            """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: line_item_labels
      level: chunk
      kind: keys
invoice:
  workflow_step: line_item_labels
  fields:
    charges:
      - fields:
          description:
            workflow_output_key: label
            prompt:
              instructions: Return the repeated charge description.
              type: str
"""
        )

        workflow = prepared.persisted_workflow_extract["workflow"]
        self.assertEqual(
            workflow["output_routes"][0]["final_path"],
            "/invoice/charges/*/description",
        )
        self.assertEqual(
            workflow["output_routes"][0]["workflow_field"],
            "charges.description",
        )
        self.assertEqual(
            workflow["leaf_fields"][0]["repetition_scope"],
            "/invoice/charges/*",
        )

    def test_prepare_extraction_yaml_routes_direct_statement_role_fields_to_root(
        self,
    ) -> None:
        prepared = prepare_extraction_yaml(
            """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: generic_step_a
      level: chunk
      kind: instruct
    - name: generic_step_b
      level: chunk
      kind: keys
  agent_chain:
    - parallel:
        - group: generic_group_a
          chain: [reconcile_statement, qa_statement, save_statement]
        - group: generic_group_b
          chain: [reconcile_meters, qa_meters, save_meters]

generic_group_a:
  workflow_step: generic_step_a
  final_value_aliases:
    generic_attr_01: generic_attr_99
  fields:
    generic_attr_01:
      workflow_output_key: generic_attr_01
      prompt:
        instructions: Return the account identifier.
        type: str

generic_group_b:
  workflow_step: generic_step_b
  fields:
    generic_attr_15:
      workflow_output_key: generic_attr_15
      prompt:
        instructions: Return the meter identifier.
        type: str
"""
        )

        workflow = prepared.persisted_workflow_extract["workflow"]
        paths_by_group = {
            (route["workflow_group"], route["workflow_field"]): route["final_path"]
            for route in workflow["output_routes"]
        }
        self.assertEqual(
            paths_by_group[("generic_group_a", "generic_attr_01")],
            "/generic_attr_01",
        )
        self.assertEqual(
            paths_by_group[("generic_group_b", "generic_attr_15")],
            "/generic_group_b/generic_attr_15",
        )

    def test_prepare_extraction_yaml_rejects_slot_metadata(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: line_item_labels
      level: chunk
      kind: keys
line_items:
  slot: chunk-keys
  workflow_step: line_item_labels
  fields:
    description:
      workflow_output_key: label
      prompt:
        instructions: Return the description.
        type: str
""",
                workflow_group_metadata_keys={"workflow_step"},
            )

        self.assertIn("slot", str(exc.exception))
        self.assertIn("workflow_step", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_reserved_workflow_final_group(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

workflow:
  fields:
    status:
      prompt:
        instructions: Return the workflow status.
        type: str
"""
            )

        self.assertIn("workflow", str(exc.exception))
        self.assertIn("reserved", str(exc.exception).lower())

    def test_prepare_extraction_yaml_rejects_invalid_custom_step_identity(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                CUSTOM_WORKFLOW_YAML.replace("line_item_labels", "line-item-labels")
            )

        self.assertIn("invalid custom step name", str(exc.exception))
        self.assertIn("line-item-labels", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_case_normalized_step_name(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                CUSTOM_WORKFLOW_YAML.replace("line_item_labels", "LineItemLabels")
            )

        self.assertIn("invalid custom step name", str(exc.exception))
        self.assertIn("LineItemLabels", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_duplicate_custom_step_name(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: line_item_labels
      level: chunk
      kind: keys
    - name: line_item_labels
      level: chunk
      kind: keys
line_items:
  workflow_step: line_item_labels
  fields:
    description:
      workflow_output_key: label
      prompt:
        instructions: Return the description.
        type: str
"""
            )

        self.assertIn("duplicate custom step name", str(exc.exception))
        self.assertIn("line_item_labels", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_reserved_custom_step_name(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                CUSTOM_WORKFLOW_YAML.replace("line_item_labels", "chunk_keys")
            )

        self.assertIn("reserved custom step name", str(exc.exception))
        self.assertIn("chunk_keys", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_missing_required_template_keys(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                CUSTOM_WORKFLOW_YAML.replace(
                    "    BILLING_HINT: Prefer values from the charge table.\n", ""
                )
            )

        self.assertIn("missing template key", str(exc.exception))
        self.assertIn("BILLING_HINT", str(exc.exception))

    def test_prepare_extraction_yaml_allows_custom_step_with_30_fields(
        self,
    ) -> None:
        fields = "\n".join(
            f"""    field_{idx}:
      workflow_output_key: label_{idx}
      prompt:
        instructions: Return field {idx}.
        type: str"""
            for idx in range(30)
        )

        prepared = prepare_extraction_yaml(
            f"""
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: grouped_fields
      level: chunk
      kind: keys
line_items:
  workflow_step: grouped_fields
  fields:
{fields}
"""
        )

        self.assertEqual(
            prepared.persisted_workflow_extract["workflow"]["field_counts"],
            {"grouped_fields": 30},
        )

    def test_prepare_extraction_yaml_rejects_custom_step_over_30_fields(
        self,
    ) -> None:
        fields = "\n".join(
            f"""    field_{idx}:
      workflow_output_key: label_{idx}
      prompt:
        instructions: Return field {idx}.
        type: str"""
            for idx in range(31)
        )

        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                f"""
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: overloaded_fields
      level: chunk
      kind: keys
line_items:
  workflow_step: overloaded_fields
  fields:
{fields}
"""
            )

        self.assertIn("overloaded_fields", str(exc.exception))
        self.assertIn("at most 30 fields", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_duplicate_output_destination(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: line_item_labels
      level: chunk
      kind: keys
line_items:
  workflow_step: line_item_labels
  fields:
    description:
      workflow_output_key: label
      prompt:
        instructions: Return the description.
        type: str
    amount:
      workflow_output_key: label
      prompt:
        instructions: Return the amount.
        type: str
"""
            )

        self.assertIn("duplicate output destination", str(exc.exception))
        self.assertIn("line_item_labels.label", str(exc.exception))

    def test_prepare_extraction_yaml_rejects_custom_step_without_routes(
        self,
    ) -> None:
        with self.assertRaises(ValueError) as exc:
            prepare_extraction_yaml(
                """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: unrouted_fields
      level: chunk
      kind: keys
invoice:
  workflow_step: unrouted_fields
  fields:
    account_number:
      prompt:
        instructions: Return the account number.
        type: str
"""
            )

        self.assertIn("output routes", str(exc.exception))
        self.assertIn("workflow_output_key", str(exc.exception))

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
