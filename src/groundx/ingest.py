import aiohttp, io, json, mimetypes, requests, typing, os
from asyncio import TimeoutError
from urllib.parse import urlparse

from json.decoder import JSONDecodeError

from .client import GroundXBase, AsyncGroundXBase
from .core.api_error import ApiError
from .core.pydantic_utilities import parse_obj_as
from .core.request_options import RequestOptions
from .errors.bad_request_error import BadRequestError
from .errors.unauthorized_error import UnauthorizedError
from .types.document import Document
from .types.ingest_remote_document import IngestRemoteDocument
from .types.ingest_response import IngestResponse

# this is used as the default value for optional parameters
OMIT = typing.cast(typing.Any, ...)


DOCUMENT_TYPE_TO_MIME = {
    "txt": "text/plain",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
    "json": "application/json",
}
MIME_TO_DOCUMENT_TYPE = {v: k for k, v in DOCUMENT_TYPE_TO_MIME.items()}


def prep_documents(
    documents: typing.Sequence[Document],
) -> typing.Tuple[
    typing.List[IngestRemoteDocument],
    typing.List[
        typing.Tuple[str, typing.Tuple[typing.Union[str, None], typing.BinaryIO, str]]
    ],
]:
    """
    Process documents and separate them into remote and local documents.
    """
    if not documents:
        raise ValueError("No documents provided for ingestion.")

    def is_valid_local_path(path: str) -> bool:
        expanded_path = os.path.expanduser(path)
        return os.path.exists(expanded_path)

    def is_valid_url(path: str) -> bool:
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    local_documents: typing.List[
        typing.Tuple[str, typing.Tuple[typing.Union[str, None], typing.BinaryIO, str]]
    ] = []
    remote_documents: typing.List[IngestRemoteDocument] = []

    for document in documents:
        if not hasattr(document, "file_path"):
            raise ValueError("Each document must have a 'file_path' attribute.")

        if is_valid_url(document.file_path):
            remote_document = IngestRemoteDocument(
                bucket_id=document.bucket_id,
                file_name=document.file_name,
                file_type=document.file_type,
                search_data=document.search_data,
                source_url=document.file_path,
            )
            remote_documents.append(remote_document)
        elif is_valid_local_path(document.file_path):
            expanded_path = os.path.expanduser(document.file_path)
            file_name = os.path.basename(expanded_path)
            mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
            file_type = MIME_TO_DOCUMENT_TYPE.get(mime_type, None)
            if document.file_type:
                file_type = document.file_type
                mime_type = DOCUMENT_TYPE_TO_MIME.get(
                    document.file_type, "application/octet-stream"
                )

            if document.file_name:
                file_name = document.file_name

            try:
                local_documents.append(
                    (
                        "blob",
                        (
                            file_name,
                            open(expanded_path, "rb"),
                            mime_type,
                        ),
                    )
                )
            except Exception as e:
                raise ValueError(f"Error reading file {expanded_path}: {e}")

            metadata = {
                "bucketId": document.bucket_id,
                "fileName": file_name,
                "fileType": file_type,
            }
            if document.search_data:
                metadata["searchData"] = document.search_data

            local_documents.append(
                (
                    "metadata",
                    (
                        f"data.json",
                        io.BytesIO(json.dumps(metadata).encode("utf-8")),
                        "application/json",
                    ),
                )
            )
        else:
            raise ValueError(f"Invalid file path: {document.file_path}")

    return remote_documents, local_documents


class GroundX(GroundXBase):
    def ingest(
        self,
        *,
        documents: typing.Sequence[Document],
        request_options: typing.Optional[RequestOptions] = None,
    ) -> IngestResponse:
        """
        Ingest local or hosted documents into a GroundX bucket.

        Parameters
        ----------
        documents : typing.Sequence[Document]

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        IngestResponse
            Documents successfully uploaded

        Examples
        --------
        from groundx import Document, GroundX

        client = GroundX(
            api_key="YOUR_API_KEY",
        )

        client.ingest(
            documents=[
                Document(
                    bucket_id=1234,
                    file_name="my_file1.txt",
                    file_path="https://my.source.url.com/file1.txt",
                    file_type="txt",
                )
            ],
        )
        """
        remote_documents, local_documents = prep_documents(documents)

        if local_documents and remote_documents:
            raise ValueError("Documents must all be either local or remote, not a mix.")

        if len(remote_documents) > 0:
            return self.documents.ingest_remote(
                documents=remote_documents,
                request_options=request_options,
            )

        timeout = self._client_wrapper.get_timeout()
        headers = self._client_wrapper.get_headers()
        base_url = self._client_wrapper.get_base_url().rstrip("/")
        follow_redirects = getattr(
            self._client_wrapper.httpx_client, "follow_redirects", True
        )

        url = f"{base_url}/v1/ingest/documents/local"
        _response = requests.post(
            url,
            files=local_documents,
            headers=headers,
            timeout=timeout,
            allow_redirects=follow_redirects,
        )

        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(
                    IngestResponse,
                    parse_obj_as(
                        type_=IngestResponse,  # type: ignore
                        object_=_response.json(),
                    ),
                )
            if _response.status_code == 400:
                raise BadRequestError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            if _response.status_code == 401:
                raise UnauthorizedError(
                    typing.cast(
                        typing.Optional[typing.Any],
                        parse_obj_as(
                            type_=typing.Optional[typing.Any],  # type: ignore
                            object_=_response.json(),
                        ),
                    )
                )
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)

        raise ApiError(status_code=_response.status_code, body=_response_json)


class AsyncGroundX(AsyncGroundXBase):
    async def ingest(
        self,
        *,
        documents: typing.Sequence[Document],
        request_options: typing.Optional[RequestOptions] = None,
    ) -> IngestResponse:
        """
        Ingest local or hosted documents into a GroundX bucket.

        Parameters
        ----------
        documents : typing.Sequence[Document]

        request_options : typing.Optional[RequestOptions]
            Request-specific configuration.

        Returns
        -------
        IngestResponse
            Documents successfully uploaded

        Examples
        --------
        import asyncio

        from groundx import AsyncGroundX, Document

        client = AsyncGroundX(
            api_key="YOUR_API_KEY",
        )

        async def main() -> None:
            await client.ingest(
                documents=[
                    Document(
                        bucket_id=1234,
                        file_name="my_file1.txt",
                        file_path="https://my.source.url.com/file1.txt",
                        file_type="txt",
                    )
                ],
            )

        asyncio.run(main())
        """
        remote_documents, local_documents = prep_documents(documents)

        if local_documents and remote_documents:
            raise ValueError("Documents must all be either local or remote, not a mix.")

        if len(remote_documents) > 0:
            return await self.documents.ingest_remote(
                documents=remote_documents,
                request_options=request_options,
            )

        timeout = self._client_wrapper.get_timeout()
        headers = self._client_wrapper.get_headers()
        base_url = self._client_wrapper.get_base_url().rstrip("/")

        url = f"{base_url}/v1/ingest/documents/local"

        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                for field_name, (file_name, file_obj, content_type) in local_documents:
                    data.add_field(
                        name=field_name,
                        value=file_obj,
                        filename=file_name,
                        content_type=content_type,
                    )

                async with session.post(
                    url, data=data, headers=headers, timeout=timeout
                ) as response:
                    if 200 <= response.status < 300:
                        response_data = await response.json()
                        return typing.cast(
                            IngestResponse,
                            parse_obj_as(
                                type_=IngestResponse,  # type: ignore
                                object_=response_data,
                            ),
                        )
                    if response.status == 400:
                        raise BadRequestError(await response.json())
                    if response.status == 401:
                        raise UnauthorizedError(await response.json())

                    raise ApiError(
                        status_code=response.status, body=await response.text()
                    )
        except TimeoutError:
            raise ApiError(status_code=408, body="Request timed out")
        except aiohttp.ClientError as e:
            raise ApiError(status_code=500, body=str(e))
