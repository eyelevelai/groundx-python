import typing

import httpx
import pytest

from groundx import AsyncGroundX, GroundX
from groundx.errors import BadRequestError, UnauthorizedError

EXTRACTION_RESULTS = [
    pytest.param({}, id="empty-object"),
    pytest.param(
        {"statement": {"total": "12.30", "missing": None}, "charges": [{"amount": 12.3}]},
        id="nested-object",
    ),
    pytest.param([], id="empty-rows"),
    pytest.param(
        [{"amount": "12.30", "missing": None}, {"amount": -2.5, "details": {"printed": True}}],
        id="rows",
    ),
]


@pytest.mark.parametrize("payload", EXTRACTION_RESULTS)
@pytest.mark.parametrize("raw", [False, True], ids=["data", "raw-response"])
def test_get_extract_preserves_object_or_rows(payload: typing.Any, raw: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/ingest/document/extract/document-1"
        return httpx.Response(200, json=payload)

    with httpx.Client(transport=httpx.MockTransport(handler)) as httpx_client:
        client = GroundX(api_key="test-key", base_url="https://api.test", httpx_client=httpx_client)
        if raw:
            response = client.documents.with_raw_response.get_extract(document_id="document-1")
            assert response.status_code == 200
            result = response.data
        else:
            result = client.documents.get_extract(document_id="document-1")

    assert type(result) is type(payload)
    assert result == payload


@pytest.mark.parametrize("payload", EXTRACTION_RESULTS)
@pytest.mark.parametrize("raw", [False, True], ids=["data", "raw-response"])
async def test_async_get_extract_preserves_object_or_rows(payload: typing.Any, raw: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/v1/ingest/document/extract/document-1"
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as httpx_client:
        client = AsyncGroundX(api_key="test-key", base_url="https://api.test", httpx_client=httpx_client)
        if raw:
            response = await client.documents.with_raw_response.get_extract(document_id="document-1")
            assert response.status_code == 200
            result = response.data
        else:
            result = await client.documents.get_extract(document_id="document-1")

    assert type(result) is type(payload)
    assert result == payload


@pytest.mark.parametrize("status,error", [(400, BadRequestError), (401, UnauthorizedError)])
def test_get_extract_preserves_errors(status: int, error: typing.Type[Exception]) -> None:
    payload = {"message": "request rejected"}
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(status, json=payload))
    ) as httpx_client:
        client = GroundX(api_key="test-key", base_url="https://api.test", httpx_client=httpx_client)
        with pytest.raises(error) as caught:
            client.documents.get_extract(document_id="document-1")
    assert typing.cast(typing.Any, caught.value).body == payload


@pytest.mark.parametrize("status,error", [(400, BadRequestError), (401, UnauthorizedError)])
async def test_async_get_extract_preserves_errors(status: int, error: typing.Type[Exception]) -> None:
    payload = {"message": "request rejected"}
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(status, json=payload))
    ) as httpx_client:
        client = AsyncGroundX(api_key="test-key", base_url="https://api.test", httpx_client=httpx_client)
        with pytest.raises(error) as caught:
            await client.documents.get_extract(document_id="document-1")
    assert typing.cast(typing.Any, caught.value).body == payload
