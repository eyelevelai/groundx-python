import requests, time, typing, os
from pathlib import Path
from tqdm import tqdm
from urllib.parse import urlparse, urlunparse

from .client import GroundXBase, AsyncGroundXBase
from .core.request_options import RequestOptions
from .csv_splitter import CSVSplitter
from .types.document import Document
from .types.ingest_remote_document import IngestRemoteDocument
from .types.ingest_response import IngestResponse
from .types.ingest_response_ingest import IngestResponseIngest

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

CSV_SPLITS = {
    ".csv": True,
}
TSV_SPLITS = {
    ".tsv": True,
}

SUFFIX_ALIASES = {
    ".jpeg": "jpg",
    ".heic": "heif",
    ".tif": "tiff",
    ".md": "txt",
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


def split_doc(file):
    if file.is_file() and (
        file.suffix.lower() in ALLOWED_SUFFIXES
        or file.suffix.lower() in SUFFIX_ALIASES
    ):
        if file.suffix.lower() in CSV_SPLITS:
            return CSVSplitter(filepath=file).split()
        elif file.suffix.lower() in TSV_SPLITS:
            return CSVSplitter(filepath=file, delimiter='\t').split()
        return [file]
    return []

class GroundX(GroundXBase):
    def ingest(
        self,
        *,
        documents: typing.Sequence[Document],
        batch_size: typing.Optional[int] = 10,
        wait_for_complete: typing.Optional[bool] = False,
        upload_api: typing.Optional[str] = "https://api.eyelevel.ai/upload/file",
        request_options: typing.Optional[RequestOptions] = None,
    ) -> IngestResponse:
        """
        Ingest local or hosted documents into a GroundX bucket.

        Parameters
        ----------
        documents : typing.Sequence[Document]

        # defines how many files to send per batch
        # ignored unless wait_for_complete is True
        batch_size : typing.Optional[int]

        # will turn on progress bar and wait for ingestion to complete
        wait_for_complete : typing.Optional[bool]

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

        if len(remote_documents) + len(local_documents) == 0:
            raise ValueError("No valid documents were provided")

        if wait_for_complete:
            with tqdm(total=len(remote_documents) + len(local_documents), desc="Ingesting Files", unit="file") as pbar:
                n = max(MIN_BATCH_SIZE, min(batch_size or MIN_BATCH_SIZE, MAX_BATCH_SIZE))

                remote_batch: typing.List[IngestRemoteDocument] = []
                ingest = IngestResponse(ingest=IngestResponseIngest(process_id="",status="queued"))

                progress = float(len(remote_documents))
                for rd in remote_documents:
                    if len(remote_batch) >= n:
                        ingest = self.documents.ingest_remote(
                            documents=remote_batch,
                            request_options=request_options,
                        )
                        ingest, progress = self._monitor_batch(ingest, progress, pbar)

                        remote_batch = []

                    remote_batch.append(rd)
                    pbar.update(0.25)
                    progress -= 0.25

                if remote_batch:
                    ingest = self.documents.ingest_remote(
                        documents=remote_batch,
                        request_options=request_options,
                    )
                    ingest, progress = self._monitor_batch(ingest, progress, pbar)


                if progress > 0:
                    pbar.update(progress)

                current_batch_size = 0
                local_batch: typing.List[Document] = []

                progress = float(len(local_documents))
                for ld in local_documents:
                    fp = Path(os.path.expanduser(ld.file_path))
                    file_size = fp.stat().st_size

                    if (current_batch_size + file_size > MAX_BATCH_SIZE_BYTES) or (len(local_batch) >= n):
                        up_docs, progress = self._process_local(local_batch, upload_api, progress, pbar)

                        ingest = self.documents.ingest_remote(
                            documents=up_docs,
                            request_options=request_options,
                        )
                        ingest, progress = self._monitor_batch(ingest, progress, pbar)

                        local_batch = []
                        current_batch_size = 0

                    local_batch.append(ld)
                    current_batch_size += file_size

                if local_batch:
                    up_docs, progress = self._process_local(local_batch, upload_api, progress, pbar)

                    ingest = self.documents.ingest_remote(
                        documents=up_docs,
                        request_options=request_options,
                    )
                    ingest, progress = self._monitor_batch(ingest, progress, pbar)

                if progress > 0:
                    pbar.update(progress)

                return ingest
        elif len(remote_documents) + len(local_documents) > MAX_BATCH_SIZE:
            raise ValueError("You have sent too many documents in this request")


        up_docs, _ = self._process_local(local_documents, upload_api)
        remote_documents.extend(up_docs)

        return self.documents.ingest_remote(
            documents=remote_documents,
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

            matched_files: typing.List[Path] = []
            for file in dir_path.rglob("*"):
                for sd in split_doc(file):
                    matched_files.append(sd)    

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
        if f".{file_extension}" in SUFFIX_ALIASES:
            file_extension = SUFFIX_ALIASES[f".{file_extension}"]

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

    def _process_local(
        self,
        local_docs,
        upload_api,
        progress = None,
        pbar = None,
    ):
        remote_docs = []
        for d in local_docs:
            splits = split_doc(Path(os.path.expanduser(d.file_path)))

            for sd in splits:
                url = self._upload_file(upload_api, sd)

                ft = d.file_type
                if sd.suffix.lower() in SUFFIX_ALIASES:
                    ft = SUFFIX_ALIASES[sd.suffix.lower()]

                fn = sd.name
                if len(splits) == 1 and d.file_name:
                    fn = d.file_name

                remote_docs.append(
                    IngestRemoteDocument(
                        bucket_id=d.bucket_id,
                        file_name=fn,
                        file_type=ft,
                        process_level=d.process_level,
                        search_data=d.search_data,
                        source_url=url,
                    )
                )

                if progress is not None and pbar is not None and pbar.update is not None:
                    pbar.update(0.25)
                    progress -= 0.25

        return remote_docs, progress

    def _monitor_batch(
        self,
        ingest,
        progress,
        pbar,
    ):
        completed_files = set()

        while (
            ingest is not None
            and ingest.ingest.status not in ["complete", "error", "cancelled"]
        ):
            time.sleep(3)
            ingest = self.documents.get_processing_status_by_id(ingest.ingest.process_id)

            if ingest.ingest.progress:
                if ingest.ingest.progress.processing and ingest.ingest.progress.processing.documents:
                    for doc in ingest.ingest.progress.processing.documents:
                        if doc.status in ["complete", "error", "cancelled"] and doc.document_id not in completed_files:
                            pbar.update(0.75)
                            progress -= 0.75
                            completed_files.add(doc.document_id)
                if ingest.ingest.progress.complete and ingest.ingest.progress.complete.documents:
                    for doc in ingest.ingest.progress.complete.documents:
                        if doc.status in ["complete", "error", "cancelled"] and doc.document_id not in completed_files:
                            pbar.update(0.75)
                            progress -= 0.75
                            completed_files.add(doc.document_id)
                if ingest.ingest.progress.cancelled and ingest.ingest.progress.cancelled.documents:
                    for doc in ingest.ingest.progress.cancelled.documents:
                        if doc.status in ["complete", "error", "cancelled"] and doc.document_id not in completed_files:
                            pbar.update(0.75)
                            progress -= 0.75
                            completed_files.add(doc.document_id)
                if ingest.ingest.progress.errors and ingest.ingest.progress.errors.documents:
                    for doc in ingest.ingest.progress.errors.documents:
                        if doc.status in ["complete", "error", "cancelled"] and doc.document_id not in completed_files:
                            pbar.update(0.75)
                            progress -= 0.75
                            completed_files.add(doc.document_id)


        if ingest.ingest.status in ["error", "cancelled"]:
            raise ValueError(f"Ingest failed with status: {ingest.ingest.status}")

        return ingest, progress

    def _upload_file_batch(
        self,
        bucket_id,
        batch,
        upload_api,
        request_options,
        pbar,
    ):
        docs = []

        progress =  float(len(batch))
        for file in batch:
            url = self._upload_file(upload_api, file)
            if file.suffix.lower() in SUFFIX_ALIASES:
                docs.append(
                    Document(
                        bucket_id=bucket_id,
                        file_name=file.name,
                        file_path=url,
                        file_type=SUFFIX_ALIASES[file.suffix.lower()],
                    ),
                )
            else:
                docs.append(
                    Document(
                        bucket_id=bucket_id,
                        file_name=file.name,
                        file_path=url,
                    ),
                )
            pbar.update(0.25)
            progress -= 0.25

        if docs:
            ingest = self.ingest(documents=docs, request_options=request_options)
            ingest, progress = self._monitor_batch(ingest, progress, pbar)

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

        if len(remote_documents) + len(local_documents) > MAX_BATCH_SIZE:
            raise ValueError("You have sent too many documents in this request")

        if len(remote_documents) + len(local_documents) == 0:
            raise ValueError("No valid documents were provided")

        for d in local_documents:
            splits = split_doc(Path(os.path.expanduser(d.file_path)))

            for sd in splits:
                url = self._upload_file(upload_api, sd)

                ft = d.file_type
                if sd.suffix.lower() in SUFFIX_ALIASES:
                    ft = SUFFIX_ALIASES[sd.suffix.lower()]

                fn = sd.name
                if len(splits) == 1 and d.file_name:
                    fn = d.file_name

                remote_documents.append(
                    IngestRemoteDocument(
                        bucket_id=d.bucket_id,
                        file_name=fn,
                        file_type=ft,
                        process_level=d.process_level,
                        search_data=d.search_data,
                        source_url=url,
                    )
                )

        return await self.documents.ingest_remote(
            documents=remote_documents,
            request_options=request_options,
        )

    def _upload_file(
        self,
        endpoint,
        file_path,
    ):
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1][1:].lower()
        if f".{file_extension}" in SUFFIX_ALIASES:
            file_extension = SUFFIX_ALIASES[f".{file_extension}"]

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
