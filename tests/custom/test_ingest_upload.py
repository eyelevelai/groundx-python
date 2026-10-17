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
    from importlib.metadata import version

    import httpx

    from groundx import Document, __version__

    package_version = version("groundx")
    assert __version__ == package_version
    path = tmp_path / "private.txt"
    path.write_bytes(b"private source")
    events = []

    def handle(request):
        events.append((request.method, request.url.path))
        assert request.headers["x-api-key"] == "test"
        assert request.headers["x-customer-key"] == "customer-test"
        assert request.headers["user-agent"] == f"groundx/{package_version}"
        assert request.headers["x-fern-sdk-name"] == "groundx"
        assert request.headers["x-fern-sdk-version"] == package_version
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

        client = AsyncGroundX(
            api_key="test",
            headers={"X-Customer-Key": "customer-test"},
            httpx_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
        )
        asyncio.run(client.ingest(documents=documents))
    else:
        client = GroundX(
            api_key="test",
            headers={"X-Customer-Key": "customer-test"},
            httpx_client=httpx.Client(transport=httpx.MockTransport(handle)),
        )
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


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "mode,count,put_seconds,reject",
    [
        ("protected", 29, 31, False),
        ("protected", 30, 31, True),
        ("public", 30, 31, False),
        ("mixed", 29, 31, False),
        ("mixed", 30, 31, True),
        ("csv", 1, 29, False),
        ("csv", 1, 31, True),
    ],
)
def test_local_batch_checks_private_expiry_before_ingest(
    monkeypatch, tmp_path, asynchronous, mode, count, put_seconds, reject
):
    import asyncio
    import datetime as dt
    import json

    import httpx

    from groundx import AsyncGroundX, Document

    path = tmp_path / ("source.csv" if mode == "csv" else "source.txt")
    path.write_text("value\n" + "synthetic\n" * 29000 if mode == "csv" else "synthetic")
    monkeypatch.setattr("groundx.csv_splitter.tempfile.tempdir", str(tmp_path))
    now = 1800000000.0
    puts = []
    submissions = []
    reservations = []

    def handle(request):
        if request.method == "GET":
            inherited = "public" if mode in ("public", "mixed") else "protected"
            return httpx.Response(
                200, json={"bucket": {"bucketId": 7, "effectiveFileAccess": {"mode": inherited, "urlTtlSeconds": 300}}}
            )
        if request.url.path.endswith("/file-upload"):
            identity = len(reservations)
            reservations.append(identity)
            return httpx.Response(
                201,
                json={
                    "uploadId": str(identity),
                    "uploadUrl": f"https://private.test/{identity}?X-Amz-Signature=exact",
                    "hostedUrl": f"https://files.test/{identity}.txt",
                    "expiresAt": dt.datetime.fromtimestamp(now + 900, dt.timezone.utc).isoformat(),
                    "method": "PUT",
                    "headers": {"Content-Type": "text/plain"},
                },
            )
        submissions.append(json.loads(request.content))
        return httpx.Response(200, json={"ingest": {"processId": "process", "status": "complete"}})

    def put(url, *, data, headers, timeout):
        nonlocal now
        assert timeout > put_seconds
        assert not any(key.lower() in ("x-api-key", "x-customer-key", "authorization") for key in headers)
        puts.append(url)
        now += put_seconds
        return _Response()

    monkeypatch.setattr(ingest.time, "time", lambda: now)
    monkeypatch.setattr(ingest.requests, "put", put)
    monkeypatch.setattr(ingest, "get_presigned_url", lambda *args: _presigned_info())
    documents = [
        Document(
            bucket_id=7,
            file_path=str(path),
            file_type="csv" if mode == "csv" else "txt",
            file_access={"mode": "protected", "urlTtlSeconds": 120}
            if mode == "mixed" and index < 16
            else None
            if mode in ("mixed", "public")
            else {"urlTtlSeconds": 120},
        )
        for index in range(count)
    ]
    transport = httpx.MockTransport(handle)

    async def run():
        if asynchronous:
            async with httpx.AsyncClient(transport=transport) as http_client:
                client = AsyncGroundX(api_key="test", httpx_client=http_client)
                return await client.ingest(
                    documents=documents, callback_url="https://callback.test", callback_data="data"
                )
        with httpx.Client(transport=transport) as http_client:
            client = GroundX(api_key="test", httpx_client=http_client)
            return client.ingest(documents=documents, callback_url="https://callback.test", callback_data="data")

    if reject:
        with pytest.raises(RuntimeError, match="expired before submission.*smaller batch"):
            asyncio.run(run())
        assert submissions == []
    else:
        result = asyncio.run(run())
        assert result.ingest.process_id == "process"
        assert len(submissions) == 1
        body = submissions[0]
        assert body["callbackUrl"] == "https://callback.test"
        assert body["callbackData"] == "data"
        assert len(body["documents"]) == (30 if mode == "csv" else count)
        expected = [
            doc.file_access.dict(by_alias=True, exclude_none=True) if doc.file_access else None for doc in documents
        ]
        assert [doc.get("fileAccess") for doc in body["documents"]] == (expected * 30 if mode == "csv" else expected)
    assert len(puts) == (30 if mode == "csv" else count)
    assert len(reservations) == (0 if mode == "public" else 16 if mode == "mixed" else 30 if mode == "csv" else count)


@pytest.mark.parametrize("directory", [False, True])
def test_monitored_batch_rejects_private_expiry_before_submission(monkeypatch, tmp_path, directory):
    import datetime as dt

    import httpx

    from groundx import Document

    path = tmp_path / "source.txt"
    path.write_text("synthetic")
    if directory:
        for index in range(29):
            (tmp_path / f"source-{index}.txt").write_text("synthetic")
    now = 1800000000.0
    submissions = []
    grants = 0

    def handle(request):
        nonlocal grants
        if request.method == "GET":
            return httpx.Response(
                200,
                json={"bucket": {"bucketId": 7, "effectiveFileAccess": {"mode": "protected", "urlTtlSeconds": 300}}},
            )
        if request.url.path.endswith("/file-upload"):
            grants += 1
            return httpx.Response(
                201,
                json={
                    "uploadId": str(grants),
                    "uploadUrl": f"https://private.test/{grants}?X-Amz-Signature=exact",
                    "hostedUrl": f"https://files.test/{grants}.txt",
                    "expiresAt": dt.datetime.fromtimestamp(now + 900, dt.timezone.utc).isoformat(),
                    "method": "PUT",
                    "headers": {"Content-Type": "text/plain"},
                },
            )
        submissions.append(request)
        return httpx.Response(200, json={"ingest": {"processId": "process", "status": "complete"}})

    def put(*args, **kwargs):
        nonlocal now
        assert kwargs["timeout"] > 31
        now += 31
        return _Response()

    monkeypatch.setattr(ingest.time, "time", lambda: now)
    monkeypatch.setattr(ingest.requests, "put", put)
    with httpx.Client(transport=httpx.MockTransport(handle)) as http_client:
        client = GroundX(api_key="test", httpx_client=http_client)
        with pytest.raises(RuntimeError, match="expired before submission.*smaller batch"):
            if directory:
                client.ingest_directory(bucket_id=7, path=str(tmp_path), batch_size=30)
            else:
                client.ingest(
                    documents=[Document(bucket_id=7, file_path=str(path), file_type="txt") for _ in range(31)],
                    wait_for_complete=True,
                    batch_size=30,
                )
    assert submissions == []
