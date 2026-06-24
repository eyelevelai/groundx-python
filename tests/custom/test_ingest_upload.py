from pathlib import Path
from typing import Any

import pytest
import requests

from groundx import GroundX
import groundx.ingest as ingest


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
