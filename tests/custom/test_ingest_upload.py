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

    def put(url: str, *, data: bytes, headers: dict[str, Any], timeout: int, allow_redirects: bool) -> _Response:
        assert allow_redirects is False
        sent_headers.update(headers)
        return _Response()

    monkeypatch.setattr(ingest.requests, "put", put)

    hosted_url = GroundX(api_key="test")._upload_file("https://api.eyelevel.ai/upload/file", path)

    assert hosted_url == "https://upload.eyelevel.ai/prod/file/ssp/file.png"
    assert "Gx-Hosted-Url" not in sent_headers
    assert "GX-HOSTED-URL" not in sent_headers


@pytest.mark.parametrize("expires_during_retry", [False, True])
def test_upload_file_retries_transient_put_errors(
    expires_during_retry: bool,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    path = tmp_path / "file.png"
    path.write_bytes(b"png")
    attempts = 0

    monkeypatch.setattr(ingest, "get_presigned_url", lambda *args: _presigned_info())
    now = 1800000000.0
    monkeypatch.setattr(ingest.time, "time", lambda: now)

    def sleep(seconds):
        nonlocal now
        now += seconds

    monkeypatch.setattr(ingest.time, "sleep", sleep)

    def put(url: str, *, data: bytes, headers: dict[str, Any], timeout: int, allow_redirects: bool) -> _Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise requests.exceptions.SSLError("transient ssl error")
        return _Response()

    monkeypatch.setattr(ingest.requests, "put", put)

    if expires_during_retry:
        with pytest.raises(ValueError, match="Upload grant has expired"):
            ingest._put_upload_file("https://storage.test/file?signature=exact", b"png", {}, now + 0.5)
        assert attempts == 1
    else:
        hosted_url = GroundX(api_key="test")._upload_file("https://api.eyelevel.ai/upload/file", path)
        assert hosted_url == "https://upload.eyelevel.ai/prod/file/ssp/file.png"
        assert attempts == 2


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("override", [None, {"mode": "public"}, {"mode": "protected"}])
def test_ingest_uses_configured_api_before_upload(monkeypatch, tmp_path, override, asynchronous):
    from importlib.metadata import version

    import httpx

    from groundx import Document, __version__

    package_version = version("groundx")
    assert __version__ == package_version
    path = tmp_path / "private.txt"
    path.write_bytes(b"private source")
    events = []
    request_options = {"additional_body_parameters": {"customFlag": "kept", "fileAccess": {"mode": "public"}}}
    storage_url = (
        "http://minio.local/exact?signature=test"
        if override == {"mode": "public"}
        else "https://private.test/exact?signature=test"
    )

    def handle(request):
        events.append((request.method, request.url.path))
        assert request.headers["x-api-key"] == "test"
        assert request.headers["x-customer-key"] == "customer-test"
        assert request.headers["user-agent"] == f"groundx/{package_version}"
        assert request.headers["x-fern-sdk-name"] == "groundx"
        assert request.headers["x-fern-sdk-version"] == package_version
        assert request.url.host == "onprem.test"
        assert request.method == "POST"
        if request.url.path.endswith("file-upload"):
            body = __import__("json").loads(request.content)
            assert body.get("fileAccess") == override
            assert body["customFlag"] == "kept"
            return httpx.Response(
                201,
                json={
                    "uploadId": "upload",
                    "uploadUrl": storage_url,
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

    def put(url, *, data, headers, timeout, allow_redirects):
        events.append(("PUT", url))
        assert allow_redirects is False
        assert url == storage_url
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
            base_url="https://onprem.test",
            headers={"X-Customer-Key": "customer-test"},
            httpx_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
        )
        asyncio.run(client.ingest(documents=documents, request_options=request_options))
    else:
        client = GroundX(
            api_key="test",
            base_url="https://onprem.test",
            headers={"X-Customer-Key": "customer-test"},
            httpx_client=httpx.Client(transport=httpx.MockTransport(handle)),
        )
        client.ingest(documents=documents, request_options=request_options)
    assert [method for method, _ in events] == ["POST", "PUT", "POST"]
    assert request_options == {"additional_body_parameters": {"customFlag": "kept", "fileAccess": {"mode": "public"}}}
    if not asynchronous:
        events.clear()
        monkeypatch.setattr(client, "_monitor_batch", lambda result, progress, pbar: (result, 0))
        client.ingest_directory(
            bucket_id=7, path=str(tmp_path), file_access=documents[0].file_access, request_options=request_options
        )
        assert [method for method, _ in events] == ["POST", "PUT", "POST"]


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("policy", ["omitted", None, {"mode": "protected", "urlTtlSeconds": 120}])
def test_direct_upload_operation_accepts_typed_initial_policy(asynchronous, policy):
    import asyncio
    import json

    import httpx

    from groundx import AsyncGroundX, FileAccessPolicy

    def handle(request):
        assert request.method == "POST"
        assert request.url == "https://onprem.test/v1/bucket/7/file-upload"
        body = json.loads(request.content)
        if policy == "omitted":
            assert "fileAccess" not in body
        else:
            assert body["fileAccess"] == policy
        return httpx.Response(
            201,
            json={
                "uploadId": "upload",
                "uploadUrl": "https://storage.test/put?signature=exact",
                "hostedUrl": "https://files.test/source",
                "expiresAt": "2099-01-01T00:00:00Z",
                "method": "PUT",
                "headers": {},
            },
        )

    kwargs = {"file_name": "source.pdf", "file_type": "pdf"}
    if policy != "omitted":
        kwargs["file_access"] = FileAccessPolicy(**policy) if policy is not None else None

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
            return await AsyncGroundX(
                api_key="test", base_url="https://onprem.test", httpx_client=transport
            ).buckets.file_upload(7, **kwargs)

    if asynchronous:
        result = asyncio.run(run())
    else:
        with httpx.Client(transport=httpx.MockTransport(handle)) as transport:
            result = GroundX(
                api_key="test", base_url="https://onprem.test", httpx_client=transport
            ).buckets.file_upload(7, **kwargs)
    assert result.hosted_url == "https://files.test/source"


def test_remote_document_policy_survives_preparation():
    from groundx import Document

    documents, local = ingest.prep_documents(
        [Document(bucket_id=7, file_path="https://source.test/doc.pdf", file_access={"mode": "protected"})]
    )
    assert not local
    assert documents[0].dict(by_alias=True)["fileAccess"]["mode"] == "protected"


def test_explicit_legacy_upload_override(monkeypatch, tmp_path):
    import httpx

    from groundx import Document

    path = tmp_path / "file.png"
    path.write_bytes(b"png")

    def handle(request):
        if request.method == "GET":
            return httpx.Response(200, json={"bucket": {"bucketId": 7}})
        assert request.url.path.endswith("remote")
        return httpx.Response(200, json={"ingest": {"processId": "process", "status": "queued"}})

    def legacy(endpoint, *args):
        assert endpoint == "https://legacy.test/upload"
        return _presigned_info()

    monkeypatch.setattr(ingest, "get_presigned_url", legacy)
    monkeypatch.setattr(ingest.requests, "put", lambda *args, **kwargs: _Response())
    client = GroundX(api_key="test", httpx_client=httpx.Client(transport=httpx.MockTransport(handle)))
    client.ingest(documents=[Document(bucket_id=7, file_path=str(path))], upload_api="https://legacy.test/upload")


@pytest.mark.parametrize("asynchronous", [False, True])
def test_protected_upload_unavailable_stops_before_native_bytes(monkeypatch, tmp_path, asynchronous):
    import asyncio

    import httpx

    from groundx import AsyncGroundX, Document
    from groundx.errors import ForbiddenError

    path = tmp_path / "private.pdf"
    path.write_bytes(b"private")
    requests = []

    def handle(request):
        requests.append(request)
        assert request.url.path.endswith("/file-upload")
        assert __import__("json").loads(request.content)["fileAccess"] == {"mode": "protected"}
        return httpx.Response(403, json={"message": "file protection unavailable"})

    monkeypatch.setattr(ingest.requests, "put", lambda *a, **kw: pytest.fail("private source uploaded"))
    documents = [Document(bucket_id=7, file_path=str(path), file_access={"mode": "protected"})]

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
            await AsyncGroundX(api_key="test", httpx_client=transport).ingest(documents=documents)

    with pytest.raises(ForbiddenError):
        if asynchronous:
            asyncio.run(run())
        else:
            GroundX(api_key="test", httpx_client=httpx.Client(transport=httpx.MockTransport(handle))).ingest(
                documents=documents
            )
    assert len(requests) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("inherited,override", [("protected", None), ("public", {"mode": "protected"})])
def test_explicit_legacy_upload_rejects_protection(monkeypatch, tmp_path, asynchronous, inherited, override):
    import asyncio

    import httpx

    from groundx import AsyncGroundX, Document

    path = tmp_path / "file.txt"
    path.write_text("source")
    monkeypatch.setattr(ingest, "get_presigned_url", lambda *a: pytest.fail("protected bytes reached legacy signer"))

    def handle(request):
        assert request.method == "GET"
        return httpx.Response(
            200, json={"bucket": {"bucketId": 7, "effectiveFileAccess": {"mode": inherited, "urlTtlSeconds": 300}}}
        )

    kwargs = {
        "documents": [Document(bucket_id=7, file_path=str(path), file_access=override)],
        "upload_api": "https://legacy.test/upload",
    }

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
            await AsyncGroundX(api_key="test", httpx_client=transport).ingest(**kwargs)

    with pytest.raises(ValueError, match="without an upload_api override"):
        if asynchronous:
            asyncio.run(run())
        else:
            GroundX(api_key="test", httpx_client=httpx.Client(transport=httpx.MockTransport(handle))).ingest(**kwargs)


def test_failed_upload_issuance_never_falls_back_to_public(monkeypatch, tmp_path):
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
def test_local_batch_preserves_submission_and_admission_errors(
    monkeypatch, tmp_path, asynchronous, mode, count, put_seconds, reject
):
    import asyncio
    import datetime as dt
    import json

    import httpx

    from groundx import AsyncGroundX, Document
    from groundx.core.api_error import ApiError

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
        if reject:
            return httpx.Response(409, json={"message": "source reservation expired"})
        return httpx.Response(200, json={"ingest": {"processId": "process", "status": "complete"}})

    def put(url, *, data, headers, timeout, allow_redirects):
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
                    documents=documents,
                    callback_url="https://callback.test",
                    callback_data="data",
                    request_options={"max_retries": 0},
                )
        with httpx.Client(transport=transport) as http_client:
            client = GroundX(api_key="test", httpx_client=http_client)
            return client.ingest(
                documents=documents,
                callback_url="https://callback.test",
                callback_data="data",
                request_options={"max_retries": 0},
            )

    if reject:
        with pytest.raises(ApiError) as error:
            asyncio.run(run())
        assert error.value.status_code == 409
        assert error.value.body == {"message": "source reservation expired"}
        assert len(submissions) == 1
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
    assert len(reservations) == (30 if mode == "csv" else count)


@pytest.mark.parametrize("directory", [False, True])
def test_monitored_batch_preserves_upstream_admission_error(monkeypatch, tmp_path, directory):
    import datetime as dt

    import httpx

    from groundx import Document
    from groundx.core.api_error import ApiError

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
        return httpx.Response(409, json={"message": "source reservation expired"})

    def put(*args, **kwargs):
        nonlocal now
        assert kwargs["timeout"] > 31
        now += 31
        return _Response()

    monkeypatch.setattr(ingest.time, "time", lambda: now)
    monkeypatch.setattr(ingest.requests, "put", put)
    with httpx.Client(transport=httpx.MockTransport(handle)) as http_client:
        client = GroundX(api_key="test", httpx_client=http_client)
        with pytest.raises(ApiError) as error:
            if directory:
                client.ingest_directory(
                    bucket_id=7, path=str(tmp_path), batch_size=30, request_options={"max_retries": 0}
                )
            else:
                client.ingest(
                    documents=[Document(bucket_id=7, file_path=str(path), file_type="txt") for _ in range(31)],
                    wait_for_complete=True,
                    batch_size=30,
                    request_options={"max_retries": 0},
                )
    assert len(submissions) == 1
    assert error.value.status_code == 409
    assert error.value.body == {"message": "source reservation expired"}


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "operation,status",
    [
        (operation, status)
        for operation, statuses in (
            ("customer.update", (403, 404, 409, 503)),
            ("buckets.update", (403, 404, 409, 503)),
            ("documents.update", (403, 404, 409, 503)),
            ("buckets.create", (403, 404, 503)),
            ("documents.ingest_remote", (403, 503)),
            ("documents.ingest_local", (403, 404, 409, 503)),
            ("documents.crawl_website", (403, 503)),
        )
        for status in statuses
    ],
)
def test_policy_operations_raise_typed_errors(asynchronous, operation, status):
    import asyncio
    import json

    import httpx

    from groundx import AsyncGroundX
    from groundx.errors import ConflictError, ForbiddenError, NotFoundError, ServiceUnavailableError

    errors = {403: ForbiddenError, 404: NotFoundError, 409: ConflictError, 503: ServiceUnavailableError}
    requests = []
    body = {"message": "policy request rejected"}

    def handle(request):
        requests.append(request)
        return httpx.Response(status, json=body, headers={"Retry-After": "1"})

    kwargs = {"request_options": {"max_retries": 0}}
    group, method = operation.split(".")
    args = []
    if method == "update":
        if group == "documents":
            kwargs["documents"] = [{"documentId": "document", "fileAccess": None, "fileAccessRevision": 7}]
        else:
            kwargs.update(file_access=None, file_access_revision=7)
            if group == "buckets":
                args = [7]
    elif method == "create":
        kwargs.update(name="private", file_access={"mode": "protected"})
    elif method == "ingest_local":
        kwargs["request"] = [
            {"blob": "test", "metadata": {"bucketId": 7, "fileName": "a.pdf", "fileAccess": {"mode": "protected"}}}
        ]
    elif method == "crawl_website":
        kwargs["websites"] = [{"bucketId": 7, "sourceUrl": "https://source.test", "fileAccess": {"mode": "protected"}}]
    else:
        kwargs["documents"] = [
            {
                "bucketId": 7,
                "sourceUrl": "https://source.test/a.pdf",
                "fileName": "a.pdf",
                "fileAccess": {"mode": "protected"},
            }
        ]

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
            client = AsyncGroundX(api_key="test", base_url="https://api.test", httpx_client=transport)
            await getattr(getattr(client, group), method)(*args, **kwargs)

    with pytest.raises(errors[status]) as error:
        if asynchronous:
            asyncio.run(run())
        else:
            with httpx.Client(transport=httpx.MockTransport(handle)) as transport:
                client = GroundX(api_key="test", base_url="https://api.test", httpx_client=transport)
                getattr(getattr(client, group), method)(*args, **kwargs)
    assert error.value.status_code == status
    assert error.value.body == body
    assert error.value.headers["retry-after"] == "1"
    assert len(requests) == 1
    if method == "update":
        sent = json.loads(requests[0].content)
        assert (sent["documents"][0] if group == "documents" else sent)["fileAccess"] is None
        assert (sent["documents"][0] if group == "documents" else sent)["fileAccessRevision"] == 7


@pytest.mark.parametrize("asynchronous", [False, True])
def test_policy_models_preserve_legacy_updates_and_initial_inheritance(asynchronous):
    import asyncio
    import json

    import httpx

    from groundx import AsyncGroundX, DocumentUpdate

    requests = []

    def handle(request):
        requests.append((request.method, request.url.path, json.loads(request.content)))
        return httpx.Response(
            200, json={"bucket": {"bucketId": 7}, "ingest": {"processId": "process", "status": "queued"}}
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
            client = AsyncGroundX(api_key="test", base_url="https://api.test", httpx_client=transport)
            await client.buckets.update(7, new_name="renamed")
            await client.documents.update(documents=[DocumentUpdate(document_id="document", file_name="renamed.pdf")])
            await client.buckets.create(name="inherited")
            await client.buckets.create(name="inherited", file_access=None)

    if asynchronous:
        asyncio.run(run())
    else:
        with httpx.Client(transport=httpx.MockTransport(handle)) as transport:
            client = GroundX(api_key="test", base_url="https://api.test", httpx_client=transport)
            client.buckets.update(7, new_name="renamed")
            client.documents.update(documents=[DocumentUpdate(document_id="document", file_name="renamed.pdf")])
            client.buckets.create(name="inherited")
            client.buckets.create(name="inherited", file_access=None)

    assert requests == [
        ("PUT", "/v1/bucket/7", {"newName": "renamed"}),
        ("PUT", "/v1/ingest/documents", {"documents": [{"documentId": "document", "fileName": "renamed.pdf"}]}),
        ("POST", "/v1/bucket", {"name": "inherited"}),
        ("POST", "/v1/bucket", {"name": "inherited", "fileAccess": None}),
    ]


@pytest.mark.parametrize("asynchronous", [False, True])
def test_file_link_serializes_page_selector_and_reads_native_grant(asynchronous):
    import asyncio
    import json

    import httpx

    from groundx import AssetSelectorCorrected, AsyncGroundX

    requests = []
    grant = {"url": "https://storage.test/page?signature=exact", "expiresAt": "2099-01-01T00:00:00Z"}

    def handle(request):
        requests.append((request.method, request.url.path, json.loads(request.content)))
        return httpx.Response(200, json=grant)

    kwargs = {"asset": AssetSelectorCorrected(kind="page", page_number=1), "expires_in_seconds": 120}

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
            client = AsyncGroundX(api_key="test", base_url="https://api.test", httpx_client=transport)
            return await client.documents.file_link("document", **kwargs)

    if asynchronous:
        response = asyncio.run(run())
    else:
        with httpx.Client(transport=httpx.MockTransport(handle)) as transport:
            client = GroundX(api_key="test", base_url="https://api.test", httpx_client=transport)
            response = client.documents.file_link("document", **kwargs)

    assert requests == [
        (
            "POST",
            "/v1/ingest/document/document/file-link",
            {"asset": {"kind": "page", "pageNumber": 1}, "expiresInSeconds": 120},
        )
    ]
    assert response.url == grant["url"]
    assert response.expires_at.isoformat() == "2099-01-01T00:00:00+00:00"
