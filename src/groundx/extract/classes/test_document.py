import pytest, typing, unittest

pytest.importorskip("PIL")

from io import BytesIO
from PIL import Image
from unittest.mock import patch

from .document import Document, DocumentRequest
from .test_groundx import TestXRay


def DR(**data: typing.Any) -> DocumentRequest:
    return DocumentRequest.model_validate(data)


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
        st1: Document = Document.from_request(
            base_url="",
            req=test_request(),
        )
        self.assertEqual(st1.file_name, "F")
        st2: Document = Document.from_request(
            base_url="",
            req=DR(
                documentID="D", fileName="F.pdf", modelID=1, processorID=1, taskID="T"
            ),
        )
        self.assertEqual(st2.file_name, "F.pdf")
        st3: Document = Document.from_request(
            base_url="",
            req=DR(documentID="D", fileName="F.", modelID=1, processorID=1, taskID="T"),
        )
        self.assertEqual(st3.file_name, "F.")


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
