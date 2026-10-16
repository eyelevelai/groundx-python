from pathlib import Path
from typing import Any

import pytest
import requests

import groundx.ingest as ingest
from groundx import GroundX


class _Response:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.text = ""
        self.headers: dict[str, str] = {}


def _presigned_info() -> dict[str, Any]:
    return {
        "URL": "https://eyelevel-upload.s3.us-west-2.amazonaws.com/prod/file/ssp/file.png?signature=test",
        "Header": {
            "Host": ["eyelevel-upload.s3.us-west-2.amazonaws.com"],
            "Gx-Hosted-Url": ["https://upload.eyelevel.ai/prod/file/ssp/file.png"],
            "Content-Type": ["image/png"],
        },
        "Method": "PUT",
    }


def test_upload_file_does_not_send_hosted_url_header_to_s3(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "file.png"
    path.write_bytes(b"png")
    sent_headers: dict[str, Any] = {}

    monkeypatch.setattr(ingest, "get_presigned_url", lambda *args: _presigned_info())

    def put(url: str, *, data: bytes, headers: dict[str, Any], timeout: int) -> _Response:
        sent_headers.update(headers)
        return _Response()

    monkeypatch.setattr(ingest.requests, "put", put)

    hosted_url = GroundX(api_key="test")._upload_file("https://api.eyelevel.ai/upload/file", path)

    assert hosted_url == "https://upload.eyelevel.ai/prod/file/ssp/file.png"
    assert "Gx-Hosted-Url" not in sent_headers
    assert "GX-HOSTED-URL" not in sent_headers


def test_upload_file_retries_transient_put_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "file.png"
    path.write_bytes(b"png")
    attempts = 0

    monkeypatch.setattr(ingest, "get_presigned_url", lambda *args: _presigned_info())
    monkeypatch.setattr(ingest.time, "sleep", lambda seconds: None)

    def put(url: str, *, data: bytes, headers: dict[str, Any], timeout: int) -> _Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise requests.exceptions.SSLError("transient ssl error")
        return _Response()

    monkeypatch.setattr(ingest.requests, "put", put)

    hosted_url = GroundX(api_key="test")._upload_file("https://api.eyelevel.ai/upload/file", path)

    assert hosted_url == "https://upload.eyelevel.ai/prod/file/ssp/file.png"
    assert attempts == 2


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("inherited,override", [("protected", None), ("public", {"mode": "protected"})])
def test_ingest_reserves_private_source_before_upload(monkeypatch, tmp_path, inherited, override, asynchronous):
    import httpx

    from groundx import Document

    path = tmp_path / "private.txt"
    path.write_bytes(b"private source")
    events = []

    def handle(request):
        events.append((request.method, request.url.path))
        assert request.headers["x-api-key"] == "test"
        if request.method == "GET":
            return httpx.Response(
                200, json={"bucket": {"bucketId": 7, "effectiveFileAccess": {"mode": inherited, "urlTtlSeconds": 300}}}
            )
        if request.url.path.endswith("file-upload"):
            return httpx.Response(
                201,
                json={
                    "uploadId": "upload",
                    "uploadUrl": "https://private.test/exact?signature=test",
                    "hostedUrl": "https://files.test/owned.txt",
                    "expiresAt": "2099-01-01T00:00:00Z",
                    "method": "PUT",
                    "headers": {"Content-Type": "text/plain"},
                },
            )
        body = __import__("json").loads(request.content)
        assert body["documents"][0]["sourceUrl"] == "https://files.test/owned.txt"
        assert body["documents"][0].get("fileAccess") == override
        return httpx.Response(200, json={"ingest": {"processId": "process", "status": "queued"}})

    def put(url, *, data, headers, timeout):
        events.append(("PUT", url))
        assert url == "https://private.test/exact?signature=test"
        assert data == b"private source"
        assert headers == {"Content-Type": "text/plain"}
        return _Response()

    monkeypatch.setattr(ingest.requests, "put", put)
    monkeypatch.setattr(ingest, "get_presigned_url", lambda *a: pytest.fail("private bytes reached public broker"))
    documents = [Document(bucket_id=7, file_path=str(path), file_access=override)]
    if asynchronous:
        import asyncio

        from groundx import AsyncGroundX

        client = AsyncGroundX(api_key="test", httpx_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)))
        asyncio.run(client.ingest(documents=documents))
    else:
        client = GroundX(api_key="test", httpx_client=httpx.Client(transport=httpx.MockTransport(handle)))
        client.ingest(documents=documents)
    assert [method for method, _ in events] == ["GET", "POST", "PUT", "POST"]
    if not asynchronous:
        events.clear()
        monkeypatch.setattr(client, "_monitor_batch", lambda result, progress, pbar: (result, 0))
        client.ingest_directory(bucket_id=7, path=str(tmp_path), file_access=documents[0].file_access)
        assert [method for method, _ in events] == ["GET", "POST", "PUT", "POST"]


def test_remote_document_policy_survives_preparation():
    from groundx import Document

    documents, local = ingest.prep_documents(
        [Document(bucket_id=7, file_path="https://source.test/doc.pdf", file_access={"mode": "protected"})]
    )
    assert not local
    assert documents[0].dict(by_alias=True)["fileAccess"]["mode"] == "protected"


def test_public_destination_keeps_legacy_upload(monkeypatch, tmp_path):
    import httpx

    from groundx import Document

    path = tmp_path / "file.png"
    path.write_bytes(b"png")

    def handle(request):
        if request.method == "GET":
            return httpx.Response(200, json={"bucket": {"bucketId": 7}})
        assert request.url.path.endswith("remote")
        return httpx.Response(200, json={"ingest": {"processId": "process", "status": "queued"}})

    monkeypatch.setattr(ingest, "get_presigned_url", lambda *args: _presigned_info())
    monkeypatch.setattr(ingest.requests, "put", lambda *args, **kwargs: _Response())
    client = GroundX(api_key="test", httpx_client=httpx.Client(transport=httpx.MockTransport(handle)))
    client.ingest(documents=[Document(bucket_id=7, file_path=str(path))])


def test_failed_policy_lookup_never_falls_back_to_public(monkeypatch, tmp_path):
    import httpx

    from groundx import Document

    path = tmp_path / "file.txt"
    path.write_bytes(b"private")
    monkeypatch.setattr(ingest, "get_presigned_url", lambda *a: pytest.fail("public fallback"))
    monkeypatch.setattr(ingest.requests, "put", lambda *a, **kw: pytest.fail("uploaded before policy check"))
    client = GroundX(
        api_key="test",
        httpx_client=httpx.Client(
            transport=httpx.MockTransport(lambda r: httpx.Response(503, json={"message": "unavailable"}))
        ),
    )
    with pytest.raises(Exception):
        client.ingest(documents=[Document(bucket_id=7, file_path=str(path))], request_options={"max_retries": 0})
