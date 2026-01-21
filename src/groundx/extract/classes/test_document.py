import pytest, typing, unittest

pytest.importorskip("PIL")

from io import BytesIO
from pathlib import Path
from PIL import Image
from unittest.mock import patch

from .document import Document, DocumentRequest
from .field import ExtractedField
from .group import Group
from ..prompt.manager import PromptManager
from ..prompt.test_manager import SAMPLE_YAML_1, SAMPLE_YAML_2, TestSource
from .test_groundx import TestXRay


def DR(**data: typing.Any) -> DocumentRequest:
    return DocumentRequest.model_validate(data)


def test_doc(prompt_manager: PromptManager) -> Document:
    return Document.from_request(
        cache_dir=Path("./cache"),
        base_url="",
        req=test_request(),
        prompt_manager=prompt_manager,
    )


def test_request() -> DocumentRequest:
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

        st1: Document = test_doc(manager)
        self.assertEqual(st1.file_name, "F")
        st2: Document = Document.from_request(
            base_url="",
            cache_dir=Path("./cache"),
            req=DR(
                documentID="D", fileName="F.pdf", modelID=1, processorID=1, taskID="T"
            ),
            prompt_manager=manager,
        )
        self.assertEqual(st2.file_name, "F.pdf")
        st3: Document = Document.from_request(
            cache_dir=Path("./cache"),
            base_url="",
            req=DR(documentID="D", fileName="F.", modelID=1, processorID=1, taskID="T"),
            prompt_manager=manager,
        )
        self.assertEqual(st3.file_name, "F.")

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


class TestDocumentRequest(unittest.TestCase):
    def test_load_images_cached(self) -> None:
        urls: typing.List[str] = [
            "http://example.com/page1.png",
            "http://example.com/page2.png",
        ]

        red_img = Image.new("RGB", (10, 10), color="red")
        buf = BytesIO()
        red_img.save(buf, format="PNG")

        st = test_request()
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
            st = test_request()
            st.load_images(urls)

            self.assertEqual(len(st.page_images), 2)
            self.assertEqual(len(st.page_image_dict), 2)
            for img in st.page_images:
                self.assertIsInstance(img, Image.Image)
                self.assertEqual(img.size, (10, 10))

    def test_load_images_error(self) -> None:
        urls = ["http://example.com/page1.png", "http://example.com/page2.png"]

        st = test_request()
        st.load_images(urls, should_sleep=False)
        self.assertEqual(len(st.page_images), 0)
        self.assertEqual(len(st.page_image_dict), 0)
