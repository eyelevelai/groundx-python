import requests, time, typing, os
from pathlib import Path
from tqdm import tqdm
from urllib.parse import urlparse, urlunparse

from .client import GroundXBase, AsyncGroundXBase
from .core.request_options import RequestOptions
from .types.document import Document
from .types.document_type import DocumentType
from .types.ingest_remote_document import IngestRemoteDocument
from .types.ingest_response import IngestResponse

# this is used as the default value for optional parameters
OMIT = typing.cast(typing.Any, ...)


DOCUMENT_TYPE_TO_MIME = {
    "bmp": "image/bmp",
    "gif": "image/gif",
    "heif": "image/heif",
    "hwp": "application/x-hwp",
    "ico": "image/vnd.microsoft.icon",
    "svg": "image/svg",
    "tiff": "image/tiff",
    "webp": "image/webp",
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

ALLOWED_SUFFIXES = {f".{k}": v for k, v in DOCUMENT_TYPE_TO_MIME.items()}

SUFFIX_ALIASES = {
    ".jpeg": ".jpg",
    ".heic": ".heif",
    ".tif": ".tiff",
}

MAX_BATCH_SIZE = 50
MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE_BYTES = 50 * 1024 * 1024

def get_presigned_url(
    endpoint: str,
    file_name: str,
    file_extension: str,
) -> typing.Dict[str, typing.Any]:
    params = {"name": file_name, "type": file_extension}
    response = requests.get(endpoint, params=params)
    response.raise_for_status()

    return response.json()

def strip_query_params(
    url: str,
) -> str:
    parsed = urlparse(url)
    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    return clean_url

def prep_documents(
    documents: typing.Sequence[Document],
) -> typing.Tuple[
    typing.List[IngestRemoteDocument],
    typing.List[Document],
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

    local_documents: typing.List[Document] = []
    remote_documents: typing.List[IngestRemoteDocument] = []

    for document in documents:
        if not hasattr(document, "file_path"):
            raise ValueError("Each document must have a 'file_path' attribute.")

        if is_valid_url(document.file_path):
            remote_document = IngestRemoteDocument(
                bucket_id=document.bucket_id,
                file_name=document.file_name,
                file_type=document.file_type,
                process_level=document.process_level,
                search_data=document.search_data,
                source_url=document.file_path,
            )
            remote_documents.append(remote_document)
        elif is_valid_local_path(document.file_path):
            local_documents.append(document)
        else:
            raise ValueError(f"Invalid file path: {document.file_path}")

    return remote_documents, local_documents


class GroundX(GroundXBase):
    def ingest(
        self,
        *,
        documents: typing.Sequence[Document],
        upload_api: typing.Optional[str] = "https://api.eyelevel.ai/upload/file",
        request_options: typing.Optional[RequestOptions] = None,
    ) -> IngestResponse:
        """
        Ingest local or hosted documents into a GroundX bucket.

        Parameters
        ----------
        documents : typing.Sequence[Document]

        # an endpoint that accepts 'name' and 'type' query params
        # and returns a presigned URL in a JSON dictionary with key 'URL'
        upload_api : typing.Optional[str]

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
            if len(remote_documents) > MAX_BATCH_SIZE:
                raise ValueError("You have sent too many documents in this request")

            return self.documents.ingest_remote(
                documents=remote_documents,
                request_options=request_options,
            )

        if len(local_documents) > MAX_BATCH_SIZE:
            raise ValueError("You have sent too many documents in this request")

        if len(local_documents) == 0:
            raise ValueError("No valid documents were provided")

        docs: typing.List[IngestRemoteDocument] = []
        for d in local_documents:
            url = self._upload_file(upload_api, Path(os.path.expanduser(d.file_path)))

            docs.append(
                IngestRemoteDocument(
                    bucket_id=d.bucket_id,
                    file_name=d.file_name,
                    file_type=d.file_type,
                    process_level=d.process_level,
                    search_data=d.search_data,
                    source_url=url,
                )
            )

        return self.documents.ingest_remote(
            documents=docs,
            request_options=request_options,
        )

    def ingest_directory(
        self,
        *,
        bucket_id: int,
        path: str,
        batch_size: typing.Optional[int] = 10,
        upload_api: typing.Optional[str] = "https://api.eyelevel.ai/upload/file",
        request_options: typing.Optional[RequestOptions] = None,
    ):
        """
        Ingest documents from a local directory into a GroundX bucket.

        Parameters
        ----------
        bucket_id : int
        path : str
        batch_size : type.Optional[int]

        # an endpoint that accepts 'name' and 'type' query params
        # and returns a presigned URL in a JSON dictionary with key 'URL'
        upload_api : typing.Optional[str]

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

        client.ingest_directory(
            bucket_id=0,
            path="/path/to/directory"
        )
        """

        def is_valid_local_directory(path: str) -> bool:
            expanded_path = os.path.expanduser(path)
            return os.path.isdir(expanded_path)

        def load_directory_files(directory: str) -> typing.List[Path]:
            dir_path = Path(directory)

            matched_files = [
                file
                for file in dir_path.rglob("*")
                if file.is_file() and (
                    file.suffix.lower() in ALLOWED_SUFFIXES
                    or file.suffix.lower() in SUFFIX_ALIASES
                )
            ]

            return matched_files      

        if bucket_id < 1:
            raise ValueError(f"Invalid bucket_id: {bucket_id}")

        if is_valid_local_directory(path) is not True:
            raise ValueError(f"Invalid directory path: {path}")

        files = load_directory_files(path)

        if len(files) < 1:
            raise ValueError(f"No supported files found in directory: {path}")

        current_batch: typing.List[Path] = []
        current_batch_size: int = 0

        n = max(MIN_BATCH_SIZE, min(batch_size or MIN_BATCH_SIZE, MAX_BATCH_SIZE))

        with tqdm(total=len(files), desc="Ingesting Files", unit="file") as pbar:
            for file in files:
                file_size = file.stat().st_size

                if (current_batch_size + file_size > MAX_BATCH_SIZE_BYTES) or (len(current_batch) >= n):
                    self._upload_file_batch(bucket_id, current_batch, upload_api, request_options, pbar)
                    current_batch = []
                    current_batch_size = 0

                current_batch.append(file)
                current_batch_size += file_size

            if current_batch:
                self._upload_file_batch(bucket_id, current_batch, upload_api, request_options, pbar)

    def _upload_file(
        self,
        endpoint,
        file_path,
    ):
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1][1:].lower()

        presigned_info = get_presigned_url(endpoint, file_name, file_extension)

        upload_url = presigned_info["URL"]
        headers = presigned_info.get("Header", {})
        method = presigned_info.get("Method", "PUT").upper()

        for key, value in headers.items():
            if isinstance(value, list):
                headers[key] = value[0]

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")

        if method == "PUT":
            upload_response = requests.put(upload_url, data=file_data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if upload_response.status_code not in (200, 201):
            raise Exception(
                f"Upload failed: {upload_response.status_code} - {upload_response.text}"
            )

        return strip_query_params(upload_url)

    def _upload_file_batch(
        self,
        bucket_id,
        batch,
        upload_api,
        request_options,
        pbar,
    ):
        docs = []

        progress = len(batch)
        for file in batch:
            url = self._upload_file(upload_api, file)
            docs.append(
                Document(
                    bucket_id=bucket_id,
                    file_path=url,
                ),
            )
            pbar.update(0.25)
            progress -= 0.25

        if docs:
            ingest = self.ingest(documents=docs, request_options=request_options)

            completed_files = set()

            while (
                ingest is not None
                and ingest.ingest.status not in ["complete", "error", "cancelled"]
            ):
                time.sleep(3)
                ingest = self.documents.get_processing_status_by_id(ingest.ingest.process_id)

                if ingest.ingest.progress and ingest.ingest.progress.processing:
                    for doc in ingest.ingest.progress.processing.documents:
                        if doc.status == "complete" and doc.document_id not in completed_files:
                            pbar.update(0.75)
                            progress -= 0.75

            if ingest.ingest.status in ["error", "cancelled"]:
                raise ValueError(f"Ingest failed with status: {ingest.ingest.status}")

            if progress > 0:
                pbar.update(progress)



class AsyncGroundX(AsyncGroundXBase):
    async def ingest(
        self,
        *,
        documents: typing.Sequence[Document],
        upload_api: str = "https://api.eyelevel.ai/upload/file",
        request_options: typing.Optional[RequestOptions] = None,
    ) -> IngestResponse:
        """
        Ingest local or hosted documents into a GroundX bucket.

        Parameters
        ----------
        documents : typing.Sequence[Document]

        # an endpoint that accepts 'name' and 'type' query params
        # and returns a presigned URL in a JSON dictionary with key 'URL'
        upload_api : typing.Optional[str]

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
            if len(remote_documents) > MAX_BATCH_SIZE:
                raise ValueError("You have sent too many documents in this request")

            return await self.documents.ingest_remote(
                documents=remote_documents,
                request_options=request_options,
            )

        if len(local_documents) > MAX_BATCH_SIZE:
            raise ValueError("You have sent too many documents in this request")

        if len(local_documents) == 0:
            raise ValueError("No valid documents were provided")

        docs: typing.List[IngestRemoteDocument] = []
        for d in local_documents:
            url = self._upload_file(upload_api, Path(os.path.expanduser(d.file_path)))

            docs.append(
                IngestRemoteDocument(
                    bucket_id=d.bucket_id,
                    file_name=d.file_name,
                    file_type=d.file_type,
                    process_level=d.process_level,
                    search_data=d.search_data,
                    source_url=url,
                )
            )

        return await self.documents.ingest_remote(
            documents=docs,
            request_options=request_options,
        )

    def _upload_file(
        self,
        endpoint,
        file_path,
    ):
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1][1:].lower()

        presigned_info = get_presigned_url(endpoint, file_name, file_extension)

        upload_url = presigned_info["URL"]
        headers = presigned_info.get("Header", {})
        method = presigned_info.get("Method", "PUT").upper()

        for key, value in headers.items():
            if isinstance(value, list):
                headers[key] = value[0]

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {e}")

        if method == "PUT":
            upload_response = requests.put(upload_url, data=file_data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if upload_response.status_code not in (200, 201):
            raise Exception(
                f"Upload failed: {upload_response.status_code} - {upload_response.text}"
            )

        return strip_query_params(upload_url)
