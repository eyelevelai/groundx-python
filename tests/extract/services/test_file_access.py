import time
import typing
from io import BytesIO
from unittest.mock import patch

import pytest
import requests
import urllib3
from ._stalled_http import stalled_urllib3_response

from groundx.extract.services import http


def _response(url: str, status: int = 200, body: bytes = b"exact\x00\n") -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response.url = url
    response.raw = urllib3.HTTPResponse(body=BytesIO(body), preload_content=False)
    return response


def _get(url: str, **kwargs: typing.Any) -> requests.Response:
    return http.bounded_file_get(url, operation="file", **kwargs)


def test_public_file_get_preserves_existing_transport_defaults() -> None:
    url = "http://public.test/page.png?existing=1"
    response = _response(url)
    with patch("requests.get", return_value=response) as get:
        assert _get(url) is response
    assert get.call_args.args == (url,)
    assert get.call_args.kwargs == {"timeout": (5.0, 30.0)}


def test_protected_file_get_accepts_unspecified_optional_deadline() -> None:
    url = "https://gateway.test/files/xray.json"
    with patch("requests.get", return_value=_response(url)) as get:
        response = _get(
            url,
            api_key="private-api-key",
            trusted_file_roots=("https://gateway.test/files",),
            operation_deadline_seconds=None,
        )
    assert response.content == b"exact\x00\n"
    assert get.call_args.kwargs["timeout"] == (5.0, 30.0)


@pytest.mark.parametrize(
    "url",
    [
        "https://wrong.test/files/xray.json",
        "http://gateway.test/files/xray.json",
        "https://gateway.test:9443/files/xray.json",
        "https://gateway.test/files-other/xray.json",
        "https://gateway.test:0/files/xray.json",
        "https://gateway.test:/files/xray.json",
        "https://[gateway.test]suffix/files/xray.json",
        "https://gateway.test/files/../outside/xray.json",
        "https://gateway.test/files/%2e%2e/outside/xray.json",
        "https://gateway.test/files/%252e%252e/outside/xray.json",
        "https://user:password@gateway.test/files/xray.json",
    ],
)
def test_file_get_excludes_credentials_outside_trusted_root(url: str) -> None:
    response = _response(url)
    with patch("requests.get", return_value=response) as get:
        result = _get(
            url,
            api_key="private-api-key",
            customer_key="customer-context",
            trusted_file_roots=("https://gateway.test/files",),
        )
    assert result.content == b"exact\x00\n"
    assert get.call_args.kwargs.get("headers") == {}
    assert "private-api-key" not in repr(get.call_args)
    assert "customer-context" not in repr(get.call_args)
    assert get.call_args.kwargs["allow_redirects"] is False
    assert response.raw.closed


@pytest.mark.parametrize(
    "url",
    [
        "https://gateway.test/files/page?X-Amz-Signature=native-secret&X-Amz-Credential=user%2Fscope&part=one%2Btwo",
        "https://gateway.test/files/page?X-Amz-Signature=",
    ],
)
def test_native_get_grant_never_receives_groundx_headers_on_trusted_host(url: str) -> None:
    response = _response(url)
    with patch("requests.get", return_value=response) as get, patch("requests.head") as head:
        result = _get(
            url,
            api_key="private-api-key",
            customer_key="customer-context",
            trusted_file_roots=("https://gateway.test/files",),
        )
    assert result.content == b"exact\x00\n"
    assert get.call_args.args == (url,)
    assert get.call_args.kwargs.get("headers") == {}
    head.assert_not_called()


@pytest.mark.parametrize(
    "root",
    [
        "http://gateway.test",
        "https://user:password@gateway.test",
        "https://gateway.test?key=secret",
        "https://gateway.test#fragment",
        "https://gateway.test/files/../elsewhere",
        "https://gateway.test/files%2Felsewhere",
        "https://gateway.test:0",
        "https://gateway.test:",
    ],
)
def test_invalid_trusted_roots_fail_before_network(root: str) -> None:
    with patch("requests.get") as get, pytest.raises(ValueError):
        _get("https://gateway.test/files/xray.json", api_key="private-api-key", trusted_file_roots=(root,))
    get.assert_not_called()


def test_customer_context_requires_api_key() -> None:
    with patch("requests.get") as get, pytest.raises(ValueError):
        _get("https://gateway.test/files/xray.json", customer_key="customer-context")
    get.assert_not_called()


def test_raw_headers_cannot_bypass_trusted_root_selection() -> None:
    with patch("requests.get") as get, pytest.raises(ValueError):
        _get("https://wrong.test/files/xray.json", headers={"X-API-Key": "private-api-key"})
    get.assert_not_called()


def test_file_redirect_is_rejected_without_following_or_reading_body() -> None:
    url = "https://gateway.test/files/xray.json?view=links"
    response = _response(url, 302)
    response.headers["Location"] = "https://attacker.test/file"
    with patch("requests.get", return_value=response) as get, pytest.raises(RuntimeError, match="redirect"):
        _get(url, api_key="private-api-key", trusted_file_roots=("https://gateway.test/files",))
    assert get.call_count == 1
    assert get.call_args.kwargs["allow_redirects"] is False
    assert response.raw.closed


def test_expired_native_grant_fails_without_secret_in_error_or_privileged_retry() -> None:
    url = "https://store.test/page?X-Amz-Signature=native-secret&X-Amz-Credential=user%2Fscope"
    response = _response(url, 403, b"expired native-secret")
    with patch("requests.get", return_value=response) as get, pytest.raises(RuntimeError) as error:
        _get(url, api_key="private-api-key", trusted_file_roots=("https://store.test",))
    assert get.call_count == 1
    assert get.call_args.args == (url,)
    assert get.call_args.kwargs.get("headers") == {}
    assert "native-secret" not in str(error.value)
    assert "private-api-key" not in repr(error.value)
    assert response.raw.closed


def test_network_error_omits_key_and_signature_in_exception_repr() -> None:
    url = "https://store.test/page?X-Amz-Signature=native-secret"
    with patch("requests.get", side_effect=requests.ConnectionError(url)), pytest.raises(RuntimeError) as error:
        _get(url, api_key="private-api-key", max_attempts=1)
    assert "native-secret" not in repr(error.value)
    assert "private-api-key" not in repr(error.value)


def test_protected_file_body_deadline_aborts_a_stalled_stream() -> None:
    url = "https://gateway.test/files/page.png"
    with stalled_urllib3_response() as raw:
        response = requests.Response()
        response.status_code = 200
        response.url = url
        response.raw = raw
        started = time.monotonic()
        with patch("requests.get", return_value=response), pytest.raises(http.BoundedRequestTimeout):
            _get(
                url,
                api_key="private-api-key",
                trusted_file_roots=("https://gateway.test/files",),
                operation_deadline_seconds=0.05,
                max_attempts=1,
            )
        assert time.monotonic() - started < 0.5
        assert raw.closed
