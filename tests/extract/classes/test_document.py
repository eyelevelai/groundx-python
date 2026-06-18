import typing
import unittest

import pytest

pytest.importorskip("PIL")

from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from ..prompt._fixtures import SAMPLE_YAML_1, SAMPLE_YAML_2, TestSource
from PIL import Image

from groundx.extract.classes.document import Document, DocumentRequest
from groundx.extract.classes.field import ExtractedField
from groundx.extract.classes.groundx import XRayDocument
from groundx.extract.classes.group import Group
from groundx.extract.classes.testing import TestXRay
from groundx.extract.prompt.manager import PromptManager

CUSTOM_WORKFLOW_YAML = """
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
        identifiers:
          - Description
        instructions: Return the printed line-item description.
        type: str
"""


CUSTOM_REPEATED_WORKFLOW_YAML = """
extraction_policy_version: v1

workflow:
  custom_steps:
    - name: charge_labels
      level: chunk
      kind: keys

invoice:
  workflow_step: charge_labels
  fields:
    charges:
      - fields:
          description:
            workflow_output_key: charge_description
            prompt:
              instructions: Return the repeated charge description.
              type: str
          amount:
            workflow_output_key: charge_amount
            prompt:
              instructions: Return the repeated charge amount.
              type: float
"""


def DR(**data: typing.Any) -> DocumentRequest:
    return DocumentRequest.model_validate(data)


def _make_doc(prompt_manager: PromptManager) -> Document:
    return Document.from_request(
        cache_dir=Path("./cache"),
        base_url="",
        req=_make_request(),
        prompt_manager=prompt_manager,
    )


def _make_request() -> DocumentRequest:
    return DR(documentID="D", fileName="F", modelID=1, processorID=1, taskID="T")


class TestDocument(unittest.TestCase):
    def setUp(self) -> None:
        patcher = patch(
            "groundx.extract.classes.document.GroundXDocument.xray", autospec=True
        )
        self.mock_xray = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_xray.return_value = TestXRay("http://test.co", [])

    def test_init_name(self) -> None:
        source = TestSource(SAMPLE_YAML_1)
        manager = PromptManager(cache_source=source, config_source=source)

        st1: Document = _make_doc(manager)
        self.assertEqual(st1.invoice_name, "F")
        st2: Document = Document.from_request(
            base_url="",
            cache_dir=Path("./cache"),
            req=DR(
                documentID="D", fileName="F.pdf", modelID=1, processorID=1, taskID="T"
            ),
            prompt_manager=manager,
        )
        self.assertEqual(st2.invoice_name, "F.pdf")
        st3: Document = Document.from_request(
            cache_dir=Path("./cache"),
            base_url="",
            req=DR(documentID="D", fileName="F.", modelID=1, processorID=1, taskID="T"),
            prompt_manager=manager,
        )
        self.assertEqual(st3.invoice_name, "F.")

    def test_inject_context_1(self) -> None:
        source = TestSource(SAMPLE_YAML_1)
        manager = PromptManager(cache_source=source, config_source=source)

        ef1 = manager.group_field("statement", "statement_date")
        if not ef1:
            self.fail("statement_date is None")
        g1 = manager.group_load("meters")
        if not g1:
            self.fail("meters is None")
        ef2 = manager.group_field("meters", "meter_number")
        if not ef2:
            self.fail("meter_number is None")

        doc = Document(
            fields={
                "meters": Group(
                    fields={
                        "meter_number": ExtractedField(
                            prompt=ef2.prompt,
                            value="456",
                        ),
                    },
                    prompt=g1.prompt,
                ),
                "statement_date": ExtractedField(
                    prompt=ef1.prompt,
                    value="123",
                ),
            },
        )
        doc.prompt_manager = manager

        self.maxDiff = None
        self.assertEqual(
            Document.model_validate(
                {
                    "fields": {
                        "statement_date": {
                            "value": "123",
                        },
                        "meters": {
                            "fields": {
                                "meter_number": {
                                    "value": "456",
                                },
                            },
                        },
                    },
                },
                context={
                    "prompt_manager": manager,
                },
            ),
            doc,
        )

    def test_inject_context_2(self) -> None:
        source = TestSource(SAMPLE_YAML_2)
        manager = PromptManager(cache_source=source, config_source=source)

        ef1 = manager.group_field("statement", "statement_date")
        if not ef1:
            self.fail("statement_date is None")
        g1 = manager.group_load("statement.meters")
        if not g1:
            self.fail("meters is None")
        ef2 = manager.group_field("statement.meters", "meter_number")
        if not ef2:
            self.fail("meter_number is None")

        doc = Document(
            fields={
                "meters": Group(
                    fields={
                        "meter_number": ExtractedField(
                            prompt=ef2.prompt,
                            value="456",
                        ),
                    },
                    prompt=g1.prompt,
                ),
                "statement_date": ExtractedField(
                    prompt=ef1.prompt,
                    value="123",
                ),
            },
        )
        doc.prompt_manager = manager

        self.maxDiff = None
        self.assertEqual(
            Document.model_validate(
                {
                    "fields": {
                        "statement_date": {
                            "value": "123",
                        },
                        "meters": {
                            "fields": {
                                "meter_number": {
                                    "value": "456",
                                },
                            },
                        },
                    },
                },
                context={
                    "prompt_manager": manager,
                },
            ),
            doc,
        )

    def test_model_dump_1(self) -> None:
        source = TestSource(SAMPLE_YAML_1)
        manager = PromptManager(cache_source=source, config_source=source)

        doc = Document(
            fields={
                "meters": Group(
                    fields={
                        "meter_number": ExtractedField(
                            value="456",
                        ),
                    },
                ),
                "statement_date": ExtractedField(
                    value="123",
                ),
            },
        )
        doc.prompt_manager = manager

        st1 = Document.model_validate(
            {
                "fields": {
                    "statement_date": {
                        "value": "123",
                    },
                    "meters": {
                        "fields": {
                            "meter_number": {
                                "value": "456",
                            },
                        },
                    },
                },
            },
            context={
                "prompt_manager": manager,
            },
        )

        self.maxDiff = None
        self.assertEqual(
            st1.model_dump(
                serialize_as_any=True,
                exclude_none=True,
                exclude={
                    "fields": {
                        "__all__": {
                            "prompt": True,
                            "fields": {"__all__": {"prompt": True}},
                        }
                    }
                },
            ),
            doc.model_dump(serialize_as_any=True, exclude_none=True),
        )

    def test_document_preserves_fixed_and_custom_readback_fields(self) -> None:
        seen: typing.List[typing.Tuple[str, typing.Any]] = []

        class CaptureDocument(Document):
            def add(self, k: str, value: typing.Any) -> typing.Union[str, None]:
                seen.append((k, value))
                return None

        source = TestSource(SAMPLE_YAML_1)
        manager = PromptManager(cache_source=source, config_source=source)
        xray = XRayDocument.model_validate(
            {
                "chunks": [
                    {
                        "chunkKeywords": '{"fixed_chunk":"yes"}',
                        "sectionSummary": '{"fixed_section":"yes"}',
                        "fileSummary": '{"fixed_file":"yes"}',
                        "customChunkOutputs": {
                            "line_item_labels": {
                                "label": {"custom_chunk": "Water service"}
                            }
                        },
                        "customSectionOutputs": {
                            "section_codes": {
                                "code": {"custom_section": "UTILITY"}
                            }
                        },
                    }
                ],
                "customDocumentOutputs": {
                    "document_flags": {
                        "needs_review": {"custom_document": False}
                    }
                },
                "documentPages": [],
                "sourceUrl": "https://example.com/doc.pdf",
            }
        )

        doc = CaptureDocument()
        doc.load_xray(
            req=_make_request(),
            xray=xray,
            prompt_manager=manager,
        )

        self.assertIn(("fixed_chunk", "yes"), seen)
        self.assertIn(("fixed_section", "yes"), seen)
        self.assertIn(("fixed_file", "yes"), seen)
        self.assertIn(("custom_chunk", "Water service"), seen)
        self.assertIn(("custom_section", "UTILITY"), seen)
        self.assertIn(("custom_document", False), seen)

    def test_document_routes_custom_outputs_to_final_workflow_paths(self) -> None:
        source = TestSource(CUSTOM_WORKFLOW_YAML)
        manager = PromptManager(cache_source=source, config_source=source)
        xray = XRayDocument.model_validate(
            {
                "chunks": [
                    {
                        "customChunkOutputs": {
                            "line_item_labels": {
                                "label": "Water service",
                            }
                        },
                    }
                ],
                "documentPages": [],
                "sourceUrl": "https://example.com/doc.pdf",
            }
        )

        doc = Document()
        doc.load_xray(
            req=_make_request(),
            xray=xray,
            prompt_manager=manager,
        )

        self.assertNotIn("label", doc.fields)
        self.assertIn("line_items", doc.fields)
        line_items = doc.fields["line_items"]
        self.assertIsInstance(line_items, Group)
        if isinstance(line_items, Group):
            description = line_items.fields["description"]
            self.assertIsInstance(description, ExtractedField)
            if isinstance(description, ExtractedField):
                self.assertEqual(description.value, "Water service")

    def test_document_routes_repeated_custom_outputs_to_one_row(self) -> None:
        source = TestSource(CUSTOM_REPEATED_WORKFLOW_YAML)
        manager = PromptManager(cache_source=source, config_source=source)
        xray = XRayDocument.model_validate(
            {
                "chunks": [
                    {
                        "customChunkOutputs": {
                            "charge_labels": {
                                "charge_description": "Water service",
                                "charge_amount": 12.34,
                            }
                        },
                    }
                ],
                "documentPages": [],
                "sourceUrl": "https://example.com/doc.pdf",
            }
        )

        doc = Document()
        doc.load_xray(
            req=_make_request(),
            xray=xray,
            prompt_manager=manager,
        )

        invoice = doc.fields["invoice"]
        self.assertIsInstance(invoice, Group)
        if isinstance(invoice, Group):
            charges = invoice.fields["charges"]
            self.assertIsInstance(charges, list)
            if isinstance(charges, list):
                self.assertEqual(len(charges), 1)
                charge = charges[0]
                self.assertIsInstance(charge, Group)
                if isinstance(charge, Group):
                    self.assertEqual(
                        charge.fields["description"],
                        ExtractedField(value="Water service"),
                    )
                    self.assertEqual(
                        charge.fields["amount"],
                        ExtractedField(value=12.34),
                    )


class TestDocumentRequest(unittest.TestCase):
    def test_load_images_cached(self) -> None:
        urls: typing.List[str] = [
            "http://example.com/page1.png",
            "http://example.com/page2.png",
        ]

        red_img = Image.new("RGB", (10, 10), color="red")
        buf = BytesIO()
        red_img.save(buf, format="PNG")

        st = _make_request()
        st.page_images = [red_img, red_img]
        st.page_image_dict = {
            urls[0]: 0,
            urls[1]: 1,
        }
        st.load_images(urls)
        self.assertEqual(len(st.page_images), 2)
        self.assertEqual(len(st.page_image_dict), 2)

    def test_load_images_download(self) -> None:
        urls = ["http://example.com/page1.png", "http://example.com/page2.png"]

        red_img = Image.new("RGB", (10, 10), color="red")
        buf = BytesIO()
        red_img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        class TestResp:
            content = img_bytes

            def raise_for_status(self) -> None:
                pass

        with patch("requests.get", return_value=TestResp()):
            st = _make_request()
            st.load_images(urls)

            self.assertEqual(len(st.page_images), 2)
            self.assertEqual(len(st.page_image_dict), 2)
            for img in st.page_images:
                self.assertIsInstance(img, Image.Image)
                self.assertEqual(img.size, (10, 10))

    def test_load_images_error(self) -> None:
        urls = ["http://example.com/page1.png", "http://example.com/page2.png"]

        st = _make_request()
        st.load_images(urls, should_sleep=False)
        self.assertEqual(len(st.page_images), 0)
        self.assertEqual(len(st.page_image_dict), 0)
