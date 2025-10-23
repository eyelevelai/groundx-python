import requests, typing, unittest
from unittest.mock import patch

from pydantic import ValidationError

from .groundx import (
    GroundXDocument,
    XRayDocument,
    Chunk,
    BoundingBox,
    DocumentPage,
)


class TestChunk:
    def __init__(self, json_str: str):
        self.sectionSummary = None
        self.suggestedText = json_str


class TestDocumentPage:
    def __init__(self, page_url: str):
        self.pageUrl = page_url


class TestXRay:
    def __init__(
        self,
        source_url: str,
        chunks: typing.Optional[typing.List[TestChunk]] = [],
        document_pages: typing.Optional[typing.List[str]] = [],
    ):
        self.chunks = chunks
        self.documentPages: typing.List[TestDocumentPage] = []
        if document_pages is not None:
            for p in document_pages:
                self.documentPages.append(TestDocumentPage(p))
        self.sourceUrl = source_url


def GD(**data: typing.Any) -> GroundXDocument:
    return GroundXDocument.model_validate(data)


class TestGroundX(unittest.TestCase):
    def make_dummy_response(
        self,
        payload: typing.Optional[typing.Dict[str, typing.Any]] = None,
        status_ok: bool = True,
        json_error: bool = False,
    ) -> typing.Any:
        class DummyResponse:
            def raise_for_status(self):
                if not status_ok:
                    raise requests.HTTPError("HTTP error!")

            def json(self):
                if json_error:
                    raise ValueError("Bad JSON!")
                return payload

        return DummyResponse()

    def test_xray_url(self):
        gx = GD(base_url="", documentID="doc123", taskID="taskABC")
        expected = "https://upload.test/layout/processed/taskABC/doc123-xray.json"
        self.assertEqual(gx.xray_url(base="https://upload.test"), expected)

    def test_download_success(self):
        payload: typing.Dict[str, typing.Any] = {
            "chunks": [],
            "documentPages": [],
            "sourceUrl": "https://example.com/foo.pdf",
        }
        dummy = self.make_dummy_response(payload=payload, status_ok=True)
        with patch("requests.get", return_value=dummy):
            gx = GD(base_url="", documentID="D", taskID="T")
            xdoc = XRayDocument.download(gx, base="https://upload.test", is_test=True)
            self.assertIsInstance(xdoc, XRayDocument)
            self.assertEqual(xdoc.chunks, [])
            self.assertEqual(xdoc.documentPages, [])
            self.assertEqual(xdoc.sourceUrl, payload["sourceUrl"])

    def test_download_request_exception(self):
        with patch("requests.get", side_effect=requests.RequestException("no network")):
            gx = GD(base_url="", documentID="D", taskID="T")
            with self.assertRaises(RuntimeError) as cm:
                XRayDocument.download(gx, base="https://upload.test", is_test=True)
            self.assertIn("Error fetching X-ray JSON", str(cm.exception))

    def test_download_http_error(self):
        dummy = self.make_dummy_response(payload={}, status_ok=False)
        with patch("requests.get", return_value=dummy):
            gx = GD(base_url="", documentID="D", taskID="T")
            with self.assertRaises(RuntimeError) as cm:
                XRayDocument.download(gx, base="https://upload.test", is_test=True)
            self.assertIn("HTTP error!", str(cm.exception))

    def test_download_json_error(self):
        dummy = self.make_dummy_response(payload=None, status_ok=True, json_error=True)
        with patch("requests.get", return_value=dummy):
            gx = GD(base_url="", documentID="D", taskID="T")
            with self.assertRaises(RuntimeError) as cm:
                XRayDocument.download(gx, base="https://upload.test", is_test=True)
            self.assertIn("Invalid JSON returned", str(cm.exception))

    def test_validation_error_on_missing_required_fields(self) -> None:
        payload: typing.Dict[str, typing.Any] = {
            "documentPages": [],
            "sourceUrl": "https://example.com/foo.pdf",
        }
        dummy = self.make_dummy_response(payload=payload, status_ok=True)
        with patch("requests.get", return_value=dummy):
            gx = GD(base_url="", documentID="D", taskID="T")
            with self.assertRaises(ValidationError) as cm:
                XRayDocument.download(gx, base="https://upload.test", is_test=True)
            self.assertIn("Field required", str(cm.exception))

    def test_xray_method_delegates_to_download(self) -> None:
        gx = GD(base_url="", documentID="X", taskID="Y")

        sentinel = object()
        with patch.object(XRayDocument, "download", return_value=sentinel):
            result = gx.xray(base="https://upload.test", is_test=True)
            self.assertIs(result, sentinel)

    def test_chunk_json_alias(self) -> None:
        raw: typing.Dict[str, typing.Any] = {
            "boundingBoxes": [],
            "chunk": "id123",
            "contentType": [],
            "json": [{"foo": "bar"}],
            "multimodalUrl": None,
            "narrative": None,
            "pageNumbers": [],
            "sectionSummary": None,
            "suggestedText": None,
            "text": None,
        }
        chunk = Chunk.model_validate(raw)
        self.assertEqual(chunk.json_, [{"foo": "bar"}])

        self.assertNotIn("json':", chunk.model_dump_json().replace('"json"', ""))

    def test_roundtrip_xray_to_models(self):
        payload: dict[str, typing.Any] = {
            "chunks": [
                {
                    "boundingBoxes": [
                        {
                            "bottomRightX": 10.0,
                            "bottomRightY": 20.0,
                            "topLeftX": 1.0,
                            "topLeftY": 2.0,
                            "corrected": True,
                            "pageNumber": 1,
                        }
                    ],
                    "chunk": "foo",
                    "contentType": ["paragraph"],
                    "json": [{"a": 1}],
                    "multimodalUrl": None,
                    "narrative": ["narr1"],
                    "pageNumbers": [1],
                    "sectionSummary": None,
                    "suggestedText": None,
                    "text": "hello",
                }
            ],
            "documentPages": [
                {
                    "chunks": [],
                    "height": 500,
                    "pageNumber": 1,
                    "pageUrl": "https://page.jpg",
                    "width": 400,
                }
            ],
            "sourceUrl": "https://doc.pdf",
            "fileKeywords": "kw",
            "fileName": "file.pdf",
            "fileType": "pdf",
            "fileSummary": "sum",
            "language": "en",
        }
        dummy = self.make_dummy_response(payload=payload, status_ok=True)
        with patch("requests.get", return_value=dummy):
            gx = GD(base_url="", documentID="D", taskID="T")
            xdoc = XRayDocument.download(gx, base="https://upload.test", is_test=True)

            self.assertEqual(xdoc.fileType, "pdf")
            self.assertEqual(xdoc.fileName, "file.pdf")
            self.assertEqual(xdoc.fileKeywords, "kw")
            self.assertEqual(xdoc.language, "en")

            self.assertEqual(len(xdoc.chunks), 1)
            chunk = xdoc.chunks[0]
            self.assertIsInstance(chunk, Chunk)
            self.assertEqual(chunk.chunk, "foo")
            bb: typing.Optional[BoundingBox] = None
            if chunk.boundingBoxes is not None and len(chunk.boundingBoxes) > 0:
                bb = chunk.boundingBoxes[0]
            self.assertIsInstance(bb, BoundingBox)
            assert bb is not None, "BoundingBox should not be None"
            self.assertTrue(bb.corrected)

            self.assertEqual(len(xdoc.documentPages), 1)
            page = xdoc.documentPages[0]
            self.assertIsInstance(page, DocumentPage)
            self.assertEqual(page.pageUrl, "https://page.jpg")


if __name__ == "__main__":
    unittest.main()
