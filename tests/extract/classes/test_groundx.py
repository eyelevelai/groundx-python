import json
import typing
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import requests
import urllib3
from pydantic import ValidationError

from groundx.extract.classes.groundx import (
    BoundingBox,
    Chunk,
    DocumentPage,
    GroundXDocument,
    XRayDocument,
)


def GD(**data: typing.Any) -> GroundXDocument:
    return GroundXDocument.model_validate(data)


def _download_xray(gx: GroundXDocument) -> XRayDocument:
    return XRayDocument.download(gx, cache_dir=Path("./cache"), base="https://upload.test", is_test=True)


class TestGroundX(unittest.TestCase):
    def test_protected_model_error_omits_nested_native_grants(self) -> None:
        url = "https://files.test/xray.json?view=links"
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response.raw = urllib3.HTTPResponse(
            body=BytesIO(b'{"sourceUrl":"https://store.test/page?X-Amz-Signature=native-secret"}'),
            preload_content=False,
        )
        with TemporaryDirectory() as directory, patch("requests.get", return_value=response):
            gx = GD(base_url="https://files.test", documentID="D", taskID="T")
            with self.assertRaises(ValidationError) as error:
                gx.xray(
                    cache_dir=Path(directory),
                    xray_url=url,
                    api_key="private-api-key",
                    trusted_file_roots=("https://files.test",),
                )
        self.assertIn("Field required", str(error.exception))
        self.assertNotIn("native-secret", repr(error.exception))
        self.assertNotIn("private-api-key", repr(error.exception))

    def test_customer_context_without_key_cannot_bypass_validation_via_cache(self) -> None:
        with TemporaryDirectory() as directory:
            (Path(directory) / "D-xray.json").write_text('{"chunks":[],"sourceUrl":"cached"}')
            gx = GD(base_url="https://files.test", documentID="D", taskID="T")
            with self.assertRaises(ValueError), patch("requests.get") as get:
                gx.xray(cache_dir=Path(directory), customer_key="customer-context")
            get.assert_not_called()

    def test_returned_presentation_refreshes_without_cache_or_storage(self) -> None:
        from unittest.mock import Mock

        url = "https://files.test/layout/processed/T/D-xray.json?view=links"
        urls = ["https://store.test/page?X-Amz-Signature=old", "https://store.test/page?X-Amz-Signature=fresh"]
        responses = []
        for asset_url in urls:
            response = requests.Response()
            response.status_code = 200
            response.url = url
            response.raw = urllib3.HTTPResponse(
                body=BytesIO(json.dumps({"chunks": [], "sourceUrl": asset_url}).encode()),
                preload_content=False,
            )
            responses.append(response)
        upload = Mock()
        with TemporaryDirectory() as directory, patch("requests.get", side_effect=responses) as get:
            cache = Path(directory) / "D-xray.json"
            cached = b'{"chunks":[],"sourceUrl":"cached"}'
            cache.write_bytes(cached)
            gx = GD(base_url="https://legacy.test", documentID="D", taskID="T")
            results = []
            for _ in range(2):
                try:
                    results.append(
                        gx.xray(
                            cache_dir=Path(directory),
                            upload=upload,
                            xray_url=url,
                            api_key="partner-secret",
                            customer_key="customer-id",
                            trusted_file_roots=("https://files.test/layout/processed",),
                        )
                    )
                except TypeError as error:
                    self.fail(f"Existing X-Ray reader cannot consume protected presentation: {error}")

            self.assertEqual([result.sourceUrl for result in results], urls)
            self.assertEqual(cache.read_bytes(), cached)
            self.assertEqual(get.call_count, 2)
            upload.get_object.assert_not_called()
            for call in get.call_args_list:
                self.assertEqual(call.args, (url,))
                self.assertEqual(
                    call.kwargs["headers"],
                    {
                        "X-API-Key": "partner-secret",
                        "X-Customer-Key": "customer-id",
                    },
                )
                self.assertFalse(call.kwargs["allow_redirects"])
                self.assertTrue(call.kwargs["stream"])
            self.assertTrue(all(response.raw.closed for response in responses))

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

    def test_download_uses_bounded_http_timeout(self):
        payload: typing.Dict[str, typing.Any] = {
            "chunks": [],
            "documentPages": [],
            "sourceUrl": "https://example.com/foo.pdf",
        }
        dummy = self.make_dummy_response(payload=payload, status_ok=True)
        with patch("requests.get", return_value=dummy) as get:
            gx = GD(base_url="", documentID="D", taskID="T")
            _download_xray(gx)

        self.assertEqual(get.call_args.kwargs["timeout"], (5.0, 30.0))

    def test_download_uses_bounded_object_store_timeout(self):
        payload: typing.Dict[str, typing.Any] = {
            "chunks": [],
            "documentPages": [],
            "sourceUrl": "https://example.com/foo.pdf",
        }

        class RecordingUpload:
            def __init__(self) -> None:
                self.kwargs: typing.Dict[str, float] = {}

            def get_object(self, _path: str, **kwargs: float) -> bytes:
                import json

                self.kwargs = kwargs
                return json.dumps(payload).encode("utf-8")

        upload = RecordingUpload()
        gx = GD(base_url="", documentID="D", taskID="T")
        with patch("requests.get") as get:
            xdoc = XRayDocument.download(
                gx,
                cache_dir=Path("./cache"),
                upload=typing.cast(typing.Any, upload),
                is_test=True,
            )

        self.assertEqual(xdoc.sourceUrl, payload["sourceUrl"])
        self.assertEqual(
            upload.kwargs,
            {
                "connect_timeout_seconds": 5.0,
                "read_timeout_seconds": 20.0,
                "total_timeout_seconds": 25.0,
            },
        )
        get.assert_not_called()

    def test_download_timeout_is_bounded(self):
        with (
            patch("requests.get", side_effect=requests.Timeout("stalled")) as get,
            patch("groundx.extract.services.http.time.sleep"),
        ):
            gx = GD(base_url="", documentID="D", taskID="T")
            with self.assertRaises(RuntimeError) as cm:
                _download_xray(gx)

        self.assertEqual(get.call_count, 2)
        self.assertIn("after 2 attempts", str(cm.exception))

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
            DocumentPage.model_validate({"chunks": [], "height": 0, "pageNumber": 1, "pageUrl": "", "width": 0}),
            DocumentPage(chunks=[], height=0, pageNumber=1, pageUrl="", width=0),
        )

        self.assertEqual(
            DocumentPage.model_validate({"height": 0, "pageNumber": 1, "pageUrl": "", "width": 0}),
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

    def test_xray_loads_custom_output_maps(self) -> None:
        xray_doc = XRayDocument.model_validate(
            {
                "chunks": [
                    {
                        "chunk": "chunk-1",
                        "contentType": ["paragraph"],
                        "customChunkOutputs": {"line_item_labels": {"label": "Water service"}},
                        "customSectionOutputs": {"section_codes": {"code": "UTILITY"}},
                    }
                ],
                "customDocumentOutputs": {"document_flags": {"needs_review": False}},
                "documentPages": [
                    {
                        "chunks": [
                            {
                                "chunk": "page-chunk-1",
                                "customChunkOutputs": {"line_item_labels": {"label": "Page local"}},
                            }
                        ],
                        "height": 500,
                        "pageNumber": 1,
                        "pageUrl": "https://page.jpg",
                        "width": 400,
                    }
                ],
                "sourceUrl": "https://doc.pdf",
            }
        )

        self.assertEqual(
            xray_doc.chunks[0].customChunkOutputs,
            {"line_item_labels": {"label": "Water service"}},
        )
        self.assertEqual(
            xray_doc.chunks[0].customSectionOutputs,
            {"section_codes": {"code": "UTILITY"}},
        )
        self.assertEqual(
            xray_doc.customDocumentOutputs,
            {"document_flags": {"needs_review": False}},
        )
        self.assertEqual(
            xray_doc.documentPages[0].chunks[0].customChunkOutputs,
            {"line_item_labels": {"label": "Page local"}},
        )

        self.assertEqual(
            xray_doc.get_extract()["chunks"][0]["customChunkOutputs"],
            {"line_item_labels": {"label": "Water service"}},
        )
        self.assertEqual(
            xray_doc.get_extract()["customDocumentOutputs"],
            {"document_flags": {"needs_review": False}},
        )

    def test_xray_method_delegates_to_download(self) -> None:
        gx = GD(base_url="", documentID="X", taskID="Y")

        sentinel = object()
        with patch.object(XRayDocument, "download", return_value=sentinel):
            result = gx.xray(cache_dir=Path("./cache"), base="https://upload.test", is_test=True)
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


if __name__ == "__main__":
    unittest.main()
