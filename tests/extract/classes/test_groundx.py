import requests, typing, unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from groundx.extract.classes.groundx import (
    GroundXDocument,
    XRayDocument,
    Chunk,
    BoundingBox,
    DocumentPage,
)


def GD(**data: typing.Any) -> GroundXDocument:
    return GroundXDocument.model_validate(data)


def _download_xray(gx: GroundXDocument) -> XRayDocument:
    return XRayDocument.download(
        gx, cache_dir=Path("./cache"), base="https://upload.test", is_test=True
    )


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
            xdoc = _download_xray(gx)
            self.assertIsInstance(xdoc, XRayDocument)
            self.assertEqual(xdoc.chunks, [])
            self.assertEqual(xdoc.documentPages, [])
            self.assertEqual(xdoc.sourceUrl, payload["sourceUrl"])

    def test_download_request_exception(self):
        with patch("requests.get", side_effect=requests.RequestException("no network")):
            gx = GD(base_url="", documentID="D", taskID="T")
            with self.assertRaises(RuntimeError) as cm:
                _download_xray(gx)
            self.assertIn("Error fetching X-ray JSON", str(cm.exception))

    def test_download_http_error(self):
        dummy = self.make_dummy_response(payload={}, status_ok=False)
        with patch("requests.get", return_value=dummy):
            gx = GD(base_url="", documentID="D", taskID="T")
            with self.assertRaises(RuntimeError) as cm:
                _download_xray(gx)
            self.assertIn("HTTP error!", str(cm.exception))

    def test_download_json_error(self):
        dummy = self.make_dummy_response(payload=None, status_ok=True, json_error=True)
        with patch("requests.get", return_value=dummy):
            gx = GD(base_url="", documentID="D", taskID="T")
            with self.assertRaises(RuntimeError) as cm:
                _download_xray(gx)
            self.assertIn("Invalid JSON returned", str(cm.exception))

    def test_DocumentPage(self):
        self.assertEqual(
            DocumentPage.model_validate(
                {
                    "chunks": None,
                    "height": 0,
                    "pageNumber": 1,
                    "pageUrl": "",
                    "width": 0,
                }
            ),
            DocumentPage(chunks=[], height=0, pageNumber=1, pageUrl="", width=0),
        )

        self.assertEqual(
            DocumentPage.model_validate(
                {"chunks": [], "height": 0, "pageNumber": 1, "pageUrl": "", "width": 0}
            ),
            DocumentPage(chunks=[], height=0, pageNumber=1, pageUrl="", width=0),
        )

        self.assertEqual(
            DocumentPage.model_validate(
                {"height": 0, "pageNumber": 1, "pageUrl": "", "width": 0}
            ),
            DocumentPage(chunks=[], height=0, pageNumber=1, pageUrl="", width=0),
        )

        self.assertEqual(
            DocumentPage.model_validate(
                {
                    "chunks": [{}],
                    "height": 0,
                    "pageNumber": 1,
                    "pageUrl": "",
                    "width": 0,
                }
            ),
            DocumentPage(
                chunks=[Chunk(boundingBoxes=[], contentType=[], pageNumbers=[])],
                height=0,
                pageNumber=1,
                pageUrl="",
                width=0,
            ),
        )

    def test_validation_error_on_missing_required_fields(self) -> None:
        payload: typing.Dict[str, typing.Any] = {
            "documentPages": [],
            "sourceUrl": "https://example.com/foo.pdf",
        }
        dummy = self.make_dummy_response(payload=payload, status_ok=True)
        with patch("requests.get", return_value=dummy):
            gx = GD(base_url="", documentID="D", taskID="T")
            with self.assertRaises(ValidationError) as cm:
                _download_xray(gx)
            self.assertIn("Field required", str(cm.exception))

    def test_xray_get_extract(self) -> None:
        xray_doc = XRayDocument.model_validate(
            {
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
                        "chunkKeywords": '{"foo":"bar"}',
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
                        "chunks": [{"text": "hello"}],
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
        )

        self.maxDiff = None
        self.assertEqual(
            xray_doc.get_extract(),
            {
                "chunks": [
                    {
                        "chunk": "foo",
                        "chunkKeywords": {"foo": "bar"},
                        "contentType": ["paragraph"],
                        "pageNumbers": [1],
                    }
                ],
                "documentPages": [
                    {
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
            },
        )

    def test_xray_method_delegates_to_download(self) -> None:
        gx = GD(base_url="", documentID="X", taskID="Y")

        sentinel = object()
        with patch.object(XRayDocument, "download", return_value=sentinel):
            result = gx.xray(
                cache_dir=Path("./cache"), base="https://upload.test", is_test=True
            )
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
            xdoc = _download_xray(gx)

            self.assertEqual(xdoc.fileType, "pdf")
            self.assertEqual(xdoc.fileName, "file.pdf")
            self.assertEqual(xdoc.fileKeywords, "kw")
            self.assertEqual(xdoc.language, "en")

            self.assertEqual(len(xdoc.chunks), 1)
            chunk = xdoc.chunks[0]
            self.assertIsInstance(chunk, Chunk)
            self.assertEqual(chunk.chunk, "foo")
            bb: typing.Optional[BoundingBox] = None
            if len(chunk.boundingBoxes) > 0:
                bb = chunk.boundingBoxes[0]
            self.assertIsInstance(bb, BoundingBox)
            assert bb is not None, "BoundingBox should not be None"
            self.assertTrue(bb.corrected)

            self.assertEqual(len(xdoc.documentPages), 1)
            page = xdoc.documentPages[0]
            self.assertIsInstance(page, DocumentPage)
            self.assertEqual(page.pageUrl, "https://page.jpg")


# ---------------------------------------------------------------------------
# AGE-148: Chunk custom output fields + extra="allow"
# ---------------------------------------------------------------------------


class TestChunkCustomOutputs(unittest.TestCase):
    def _base_chunk(self) -> typing.Dict[str, typing.Any]:
        return {
            "boundingBoxes": [],
            "contentType": [],
            "pageNumbers": [],
        }

    def test_custom_chunk_outputs_are_parsed(self) -> None:
        """Task 5.1(a): customChunkOutputs round-trips through Chunk."""
        data = {**self._base_chunk(), "customChunkOutputs": {"adp_chunk_01": {"plan_type": "401k"}}}
        chunk = Chunk(**data)
        self.assertEqual(chunk.customChunkOutputs, {"adp_chunk_01": {"plan_type": "401k"}})

    def test_custom_section_outputs_are_parsed(self) -> None:
        """Task 5.1(b): customSectionOutputs round-trips through Chunk."""
        data = {**self._base_chunk(), "customSectionOutputs": {"adp_section_01": {"section_name": "Contributions"}}}
        chunk = Chunk(**data)
        self.assertEqual(chunk.customSectionOutputs, {"adp_section_01": {"section_name": "Contributions"}})

    def test_chunk_without_custom_outputs_has_none_fields(self) -> None:
        """Task 5.1(c): chunk without either key has both fields as None."""
        chunk = Chunk(**self._base_chunk())
        self.assertIsNone(chunk.customChunkOutputs)
        self.assertIsNone(chunk.customSectionOutputs)

    def test_chunk_with_unknown_field_does_not_raise(self) -> None:
        """Task 5.1(d): unknown field does NOT raise ValidationError."""
        data = {**self._base_chunk(), "futureField": "value"}
        try:
            chunk = Chunk(**data)
        except ValidationError as exc:
            self.fail(f"Chunk raised ValidationError on unknown field: {exc}")


# ---------------------------------------------------------------------------
# AGE-148: XRayDocument custom output fields + extra="allow"
# ---------------------------------------------------------------------------


class TestXRayDocumentCustomOutputs(unittest.TestCase):
    def _base_xray(self) -> typing.Dict[str, typing.Any]:
        return {
            "chunks": [],
            "documentPages": [],
            "sourceUrl": "https://example.com/doc.pdf",
        }

    def test_custom_document_outputs_are_parsed(self) -> None:
        """Task 6.1(a): customDocumentOutputs round-trips through XRayDocument."""
        data = {**self._base_xray(), "customDocumentOutputs": {"adp_doc_01": {"plan_name": "ADP 401k"}}}
        xray = XRayDocument(**data)
        self.assertEqual(xray.customDocumentOutputs, {"adp_doc_01": {"plan_name": "ADP 401k"}})

    def test_xray_without_custom_outputs_has_none_field(self) -> None:
        """Task 6.1(b): XRayDocument without the key has customDocumentOutputs as None."""
        xray = XRayDocument(**self._base_xray())
        self.assertIsNone(xray.customDocumentOutputs)

    def test_xray_with_unknown_field_does_not_raise(self) -> None:
        """Task 6.1(c): unknown document-level field does NOT raise ValidationError."""
        data = {**self._base_xray(), "newTopLevelField": "value"}
        try:
            XRayDocument(**data)
        except ValidationError as exc:
            self.fail(f"XRayDocument raised ValidationError on unknown field: {exc}")

    def test_xray_download_exposes_custom_chunk_outputs(self) -> None:
        """Task 6.1(d): XRayDocument.download returns model where chunk customChunkOutputs
        is accessible when the X-Ray JSON contains it."""
        from unittest.mock import patch

        payload = {
            "chunks": [
                {
                    "boundingBoxes": [],
                    "contentType": [],
                    "pageNumbers": [],
                    "customChunkOutputs": {"my_step": {"result": 1}},
                }
            ],
            "documentPages": [],
            "sourceUrl": "https://example.com/doc.pdf",
        }

        class DummyResp:
            def raise_for_status(self):
                pass

            def json(self):
                return payload

        from groundx.extract.classes.groundx import GroundXDocument
        gx = GroundXDocument.model_validate(
            {"base_url": "", "documentID": "D", "taskID": "T"}
        )
        with patch("requests.get", return_value=DummyResp()):
            xdoc = XRayDocument.download(
                gx, cache_dir=Path("./cache"), base="https://upload.test", is_test=True
            )

        self.assertEqual(xdoc.chunks[0].customChunkOutputs, {"my_step": {"result": 1}})


if __name__ == "__main__":
    unittest.main()
