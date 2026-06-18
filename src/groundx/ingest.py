import os
import time
import typing
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import requests
from .client import AsyncGroundXBase, GroundXBase
from .core.request_options import RequestOptions
from .csv_splitter import CSVSplitter
from .types.document import Document
from .types.ingest_remote_document import IngestRemoteDocument
from .types.ingest_response import IngestResponse
from .types.ingest_status import IngestStatus
from tqdm import tqdm

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
    ".jfi": "jpg",
    ".jfif": "jpg",
    ".jpe": "jpg",
    ".jpeg": "jpg",
    ".heic": "heif",
    ".tif": "tiff",
    ".md": "txt",
}

MAX_BATCH_SIZE = 50
MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE_BYTES = 50 * 1024 * 1024


def _import_extraction_workflows() -> typing.Any:
    try:
        from .extract import workflows as extraction_workflows
    except ImportError as exc:
        raise ImportError(
            "Extraction workflow helpers require the extract extra. Install it with `pip install groundx[extract]`."
        ) from exc

    return extraction_workflows


def _select_extraction_definition_loader_source(
    *,
    workflow_id: typing.Any,
    path: typing.Any,
    yaml_text: typing.Any,
    mapping: typing.Any,
    prepared: typing.Any,
    mapping_kind: typing.Optional[str],
    request_options: typing.Optional[RequestOptions],
) -> str:
    yaml_sources = {
        "path": path,
        "yaml_text": yaml_text,
        "mapping": mapping,
        "prepared": prepared,
    }
    if workflow_id is not OMIT:
        if mapping_kind is not None:
            raise ValueError("mapping_kind is only valid when mapping is the selected source")
        return "workflow_id"

    selected = [name for name, value in yaml_sources.items() if value is not OMIT]
    if len(selected) != 1:
        source_names = ", ".join(("workflow_id", *yaml_sources.keys()))
        if not selected:
            raise ValueError(f"expected exactly one source: {source_names}")
        conflicts = ", ".join(selected)
        raise ValueError(f"expected exactly one YAML source from {source_names}; received {conflicts}")
    if mapping_kind is not None and selected[0] != "mapping":
        raise ValueError("mapping_kind is only valid when mapping is the selected source")
    if request_options is not None:
        raise ValueError("request_options is only valid when workflow_id is selected")
    return selected[0]


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
                filter=document.filter,
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


def split_doc(file: Path) -> typing.List[Path]:
    if file.is_file() and (file.suffix.lower() in ALLOWED_SUFFIXES or file.suffix.lower() in SUFFIX_ALIASES):
        if file.suffix.lower() in CSV_SPLITS:
            return CSVSplitter(filepath=file).split()
        elif file.suffix.lower() in TSV_SPLITS:
            return CSVSplitter(filepath=file, delimiter="\t").split()
        return [file]
    return []


class GroundX(GroundXBase):
    def load_extraction_definition(
        self,
        *,
        workflow_id: typing.Any = OMIT,
        path: typing.Any = OMIT,
        yaml_text: typing.Any = OMIT,
        mapping: typing.Any = OMIT,
        prepared: typing.Any = OMIT,
        mapping_kind: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Any:
        """
        Load an extraction definition from YAML/prepared input or an existing workflow ID.

        Extraction workflow helpers require the extract extra:
        `pip install groundx[extract]`.

        Parameters
        ----------
        workflow_id : typing.Any
            Existing GroundX workflow ID to load.
        path : typing.Any
            Path to an authored extraction YAML file. This is the common
            application path.
        yaml_text : typing.Any
            Authored extraction YAML as a string.
        mapping : typing.Any
            Authored extraction YAML as a mapping, or an existing workflow
            extract mapping when `mapping_kind="workflow_extract"` is set.
        prepared : typing.Any
            A `PreparedExtractionYaml` returned by `prepare_extraction_yaml`.
        mapping_kind : typing.Optional[str]
            Use `"workflow_extract"` only when `mapping` is an existing workflow
            extract payload. Omit it for authored YAML-shaped mappings.
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration forwarded to the generated workflow
            client. Valid only with `workflow_id`.

        Returns
        -------
        typing.Any
            An `ExtractionDefinition`.

        Examples
        --------
        >>> definition = client.load_extraction_definition(path="statement.yaml")
        >>> existing = client.load_extraction_definition(workflow_id="workflow-id")

        Notes
        -----
        When `workflow_id` is provided, it takes precedence over YAML/prepared
        inputs. Otherwise pass exactly one of `path`, `yaml_text`, `mapping`, or
        `prepared`.
        """
        selected = _select_extraction_definition_loader_source(
            workflow_id=workflow_id,
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
            request_options=request_options,
        )
        if selected == "workflow_id":
            return self.load_extraction_definition_from_workflow(
                typing.cast(str, workflow_id),
                request_options=request_options,
            )
        return self.load_extraction_definition_from_yaml(
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
        )

    def load_extraction_definition_from_yaml(
        self,
        *,
        path: typing.Any = OMIT,
        yaml_text: typing.Any = OMIT,
        mapping: typing.Any = OMIT,
        prepared: typing.Any = OMIT,
        mapping_kind: typing.Optional[str] = None,
    ) -> typing.Any:
        """
        Load an extraction definition from a YAML path, YAML text, mapping, or prepared object.

        Extraction workflow helpers require the extract extra:
        `pip install groundx[extract]`.

        Parameters
        ----------
        path : typing.Any
            Path to an authored extraction YAML file. This is the common
            application path.
        yaml_text : typing.Any
            Authored extraction YAML as a string.
        mapping : typing.Any
            Authored extraction YAML as a mapping, or an existing workflow
            extract mapping when `mapping_kind="workflow_extract"` is set.
        prepared : typing.Any
            A `PreparedExtractionYaml` returned by `prepare_extraction_yaml`.
        mapping_kind : typing.Optional[str]
            Use `"workflow_extract"` only when `mapping` is an existing workflow
            extract payload. Omit it for authored YAML-shaped mappings.

        Returns
        -------
        typing.Any
            An `ExtractionDefinition` containing the persisted workflow extract
            and workflow-level settings such as template, custom steps, output
            routes, and leaf fields.

        Examples
        --------
        >>> definition = client.load_extraction_definition_from_yaml(path="statement.yaml")

        Prefer `load_extraction_definition(...)` for new code when the source
        may be either YAML or an existing workflow ID.
        """
        extraction_workflows = _import_extraction_workflows()
        return extraction_workflows.load_extraction_definition_from_yaml(
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
        )

    def load_extraction_definition_from_workflow(
        self,
        workflow_id: str,
        *,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Any:
        """
        Load an extraction definition from an existing workflow ID.

        Extraction workflow helpers require the extract extra:
        `pip install groundx[extract]`.

        Parameters
        ----------
        workflow_id : str
            Existing GroundX workflow ID.
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration forwarded to the generated workflow
            client.

        Returns
        -------
        typing.Any
            An `ExtractionDefinition` loaded from the workflow response.
            Workflows that only contain execution-ready extract JSON return a
            definition with `prepared=None`.

        Examples
        --------
        >>> definition = client.load_extraction_definition_from_workflow("workflow-id")

        Prefer `load_extraction_definition(workflow_id=...)` for new code when
        the source may be either YAML or an existing workflow ID.

        Notes
        -----
        Workflows that only contain execution-ready extract JSON return a
        definition with `prepared=None`; the create/update payload remains
        reusable, but authored YAML metadata is unavailable.
        """
        extraction_workflows = _import_extraction_workflows()
        response = self.workflows.get(workflow_id, request_options=request_options)
        return extraction_workflows.load_extraction_definition_from_workflow_response(
            workflow_id,
            response,
        )

    def create_extraction_workflow(
        self,
        *,
        definition: typing.Any = OMIT,
        path: typing.Any = OMIT,
        yaml_text: typing.Any = OMIT,
        mapping: typing.Any = OMIT,
        prepared: typing.Any = OMIT,
        mapping_kind: typing.Optional[str] = None,
        name: typing.Optional[str] = None,
        chunk_strategy: typing.Any = OMIT,
        section_strategy: typing.Any = OMIT,
        steps: typing.Any = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Any:
        """
        Create an extraction workflow from a definition or YAML/prepared source.

        Extraction workflow helpers require the extract extra:
        `pip install groundx[extract]`.

        Parameters
        ----------
        definition : typing.Any
            An `ExtractionDefinition` returned by an extraction definition
            loader.
        path : typing.Any
            Path to an authored extraction YAML file.
        yaml_text : typing.Any
            Authored extraction YAML as a string.
        mapping : typing.Any
            Authored YAML-shaped mapping, or a workflow extract mapping when
            `mapping_kind="workflow_extract"` is set.
        prepared : typing.Any
            A `PreparedExtractionYaml` returned by `prepare_extraction_yaml`.
        mapping_kind : typing.Optional[str]
            Use `"workflow_extract"` only when `mapping` is an existing workflow
            extract payload.
        name : typing.Optional[str]
            Workflow name. Required for create.
        chunk_strategy : typing.Any
            Optional workflow chunk strategy override.
        section_strategy : typing.Any
            Optional workflow section strategy override.
        steps : typing.Any
            Optional fixed workflow step overlay. When omitted and the
            definition has custom steps, fixed default extraction steps are
            disabled.
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration forwarded to the generated workflow
            client.

        Returns
        -------
        typing.Any
            The generated workflow create response.

        Examples
        --------
        >>> workflow = client.create_extraction_workflow(
        ...     path="statement.yaml",
        ...     name="statement extraction",
        ... )
        >>> client.workflows.add_to_id(id=bucket_id, workflow_id=workflow.workflow.workflow_id)

        Notes
        -----
        This delegates to `client.workflows.create(...)` after loading the
        extraction definition and copying workflow template/custom-step settings.
        If `definition` is provided, it takes precedence over YAML/prepared
        inputs. Otherwise pass exactly one of `path`, `yaml_text`, `mapping`, or
        `prepared`.
        Assign the returned workflow to a bucket, group, or account explicitly.
        """
        extraction_workflows = _import_extraction_workflows()
        resolved = extraction_workflows.resolve_extraction_definition_source(
            definition=definition,
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
        )
        kwargs = extraction_workflows.workflow_kwargs_from_extraction_definition(
            resolved,
            name=name,
            require_name=True,
            chunk_strategy=chunk_strategy,
            section_strategy=section_strategy,
            steps=steps,
            request_options=request_options,
        )
        extraction_workflows.ensure_workflow_method_supports_kwargs(
            self.workflows.create,
            kwargs,
        )
        return self.workflows.create(**kwargs)

    def update_extraction_workflow(
        self,
        workflow_id: str,
        *,
        definition: typing.Any = OMIT,
        path: typing.Any = OMIT,
        yaml_text: typing.Any = OMIT,
        mapping: typing.Any = OMIT,
        prepared: typing.Any = OMIT,
        mapping_kind: typing.Optional[str] = None,
        name: typing.Any = OMIT,
        chunk_strategy: typing.Any = OMIT,
        section_strategy: typing.Any = OMIT,
        steps: typing.Any = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Any:
        """
        Update an extraction workflow from a definition or YAML/prepared source.

        Extraction workflow helpers require the extract extra:
        `pip install groundx[extract]`.

        Parameters
        ----------
        workflow_id : str
            Existing workflow ID to update.
        definition : typing.Any
            An `ExtractionDefinition` returned by an extraction definition
            loader.
        path : typing.Any
            Path to an authored extraction YAML file.
        yaml_text : typing.Any
            Authored extraction YAML as a string.
        mapping : typing.Any
            Authored YAML-shaped mapping, or a workflow extract mapping when
            `mapping_kind="workflow_extract"` is set.
        prepared : typing.Any
            A `PreparedExtractionYaml` returned by `prepare_extraction_yaml`.
        mapping_kind : typing.Optional[str]
            Use `"workflow_extract"` only when `mapping` is an existing workflow
            extract payload.
        name : typing.Any
            Optional workflow name to send with the full update payload.
        chunk_strategy : typing.Any
            Optional workflow chunk strategy override.
        section_strategy : typing.Any
            Optional workflow section strategy override.
        steps : typing.Any
            Optional fixed workflow step overlay. When omitted and the
            definition has custom steps, fixed default extraction steps are
            disabled.
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration forwarded to the generated workflow
            client.

        Returns
        -------
        typing.Any
            The generated workflow update response.

        Examples
        --------
        >>> client.update_extraction_workflow(
        ...     "workflow-id",
        ...     path="statement.yaml",
        ...     name="statement extraction",
        ... )

        Notes
        -----
        Update sends the full extraction workflow settings, not a patch. Pass
        the YAML or definition again so custom workflow settings are preserved.
        If `definition` is provided, it takes precedence over YAML/prepared
        inputs. Otherwise pass exactly one of `path`, `yaml_text`, `mapping`, or
        `prepared`.
        """
        extraction_workflows = _import_extraction_workflows()
        resolved = extraction_workflows.resolve_extraction_definition_source(
            definition=definition,
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
        )
        kwargs = extraction_workflows.workflow_kwargs_from_extraction_definition(
            resolved,
            name=name,
            chunk_strategy=chunk_strategy,
            section_strategy=section_strategy,
            steps=steps,
            request_options=request_options,
        )
        extraction_workflows.ensure_workflow_method_supports_kwargs(
            self.workflows.update,
            kwargs,
        )
        return self.workflows.update(workflow_id, **kwargs)

    def ingest(
        self,
        *,
        documents: typing.Sequence[Document],
        batch_size: int = 10,
        wait_for_complete: bool = False,
        upload_api: str = "https://api.eyelevel.ai/upload/file",
        callback_url: typing.Optional[str] = None,
        callback_data: typing.Optional[str] = None,
        override_batch_size: typing.Optional[bool] = False,
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

        # an endpoint that will receive processing event updates as POST
        callback_url : typing.Optional[str]

        # a string that is returned, along with processing event updates,
        # to the callback URL.
        callback_data : typing.Optional[str]

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

        max_n = MAX_BATCH_SIZE
        if override_batch_size:
            max_n = 1000

        if wait_for_complete:
            with tqdm(
                total=len(remote_documents) + len(local_documents),
                desc="Ingesting Files",
                unit="file",
            ) as pbar:
                n = max(MIN_BATCH_SIZE, min(batch_size or MIN_BATCH_SIZE, max_n))

                remote_batch: typing.List[IngestRemoteDocument] = []
                ingest = IngestResponse(ingest=IngestStatus(process_id="", status="queued"))

                progress = float(len(remote_documents))
                for rd in remote_documents:
                    if len(remote_batch) >= n:
                        ingest = self.documents.ingest_remote(
                            documents=remote_batch,
                            callback_url=callback_url,
                            callback_data=callback_data,
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
                        callback_data=callback_data,
                        callback_url=callback_url,
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
                            callback_url=callback_url,
                            callback_data=callback_data,
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
                        callback_data=callback_data,
                        callback_url=callback_url,
                        request_options=request_options,
                    )
                    ingest, progress = self._monitor_batch(ingest, progress, pbar)

                if progress > 0:
                    pbar.update(progress)

                return ingest
        elif len(remote_documents) + len(local_documents) > max_n:
            raise ValueError("You have sent too many documents in this request")

        up_docs, _ = self._process_local(local_documents, upload_api, 0, None)
        remote_documents.extend(up_docs)

        return self.documents.ingest_remote(
            documents=remote_documents,
            callback_url=callback_url,
            callback_data=callback_data,
            request_options=request_options,
        )

    def ingest_directory(
        self,
        *,
        bucket_id: int,
        path: str,
        batch_size: int = 10,
        upload_api: str = "https://api.eyelevel.ai/upload/file",
        callback_url: typing.Optional[str] = None,
        callback_data: typing.Optional[str] = None,
        override_batch_size: typing.Optional[bool] = False,
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

        # an endpoint that will receive processing event updates as POST
        callback_url : typing.Optional[str]

        # a string that is returned, along with processing event updates,
        # to the callback URL.
        callback_data : typing.Optional[str]

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

        max_n = MAX_BATCH_SIZE
        if override_batch_size:
            max_n = 1000

        n = max(MIN_BATCH_SIZE, min(batch_size or MIN_BATCH_SIZE, max_n))

        with tqdm(total=len(files), desc="Ingesting Files", unit="file") as pbar:
            for file in files:
                file_size = file.stat().st_size

                if (current_batch_size + file_size > MAX_BATCH_SIZE_BYTES) or (len(current_batch) >= n):
                    self._upload_file_batch(
                        bucket_id,
                        current_batch,
                        upload_api,
                        callback_url,
                        callback_data,
                        request_options,
                        pbar,
                    )
                    current_batch = []
                    current_batch_size = 0

                current_batch.append(file)
                current_batch_size += file_size

            if current_batch:
                self._upload_file_batch(
                    bucket_id,
                    current_batch,
                    upload_api,
                    callback_url,
                    callback_data,
                    request_options,
                    pbar,
                )

    def _upload_file(
        self,
        endpoint: str,
        file_path: Path,
    ) -> str:
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1][1:].lower()
        if f".{file_extension}" in SUFFIX_ALIASES:
            file_extension = SUFFIX_ALIASES[f".{file_extension}"]

        presigned_info = get_presigned_url(endpoint, file_name, file_extension)

        upload_url = presigned_info["URL"]
        hd = presigned_info.get("Header", {})
        method = presigned_info.get("Method", "PUT").upper()

        headers: typing.Dict[str, typing.Any] = {}
        for key, value in hd.items():
            if isinstance(value, list):
                headers[key.upper()] = value[0]

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
            raise Exception(f"Upload failed: {upload_response.status_code} - {upload_response.text}")

        if "GX-HOSTED-URL" in headers:
            return headers["GX-HOSTED-URL"]

        return strip_query_params(upload_url)

    def _process_local(
        self,
        local_docs: typing.List[Document],
        upload_api: str,
        progress: float,
        pbar: typing.Optional[typing.Any] = None,
    ) -> typing.Tuple[typing.List[IngestRemoteDocument], float]:
        remote_docs: typing.List[IngestRemoteDocument] = []
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
                        filter=d.filter,
                        process_level=d.process_level,
                        search_data=d.search_data,
                        source_url=url,
                    )
                )

                progress -= 0.25
                if pbar is not None and pbar.update is not None:
                    pbar.update(0.25)

        return remote_docs, progress

    def _monitor_batch(
        self,
        ingest: IngestResponse,
        progress: float,
        pbar: typing.Any,
    ) -> typing.Tuple[IngestResponse, float]:
        completed_files: typing.Set[str] = set()

        while ingest.ingest.status not in ["complete", "error", "cancelled"]:
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
        bucket_id: int,
        batch: typing.List[Path],
        upload_api: str,
        callback_url: typing.Optional[str],
        callback_data: typing.Optional[str],
        request_options: typing.Optional[RequestOptions],
        pbar: typing.Any,
    ) -> None:
        docs: typing.List[Document] = []

        progress = float(len(batch))
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
            ingest = self.ingest(
                documents=docs,
                callback_data=callback_data,
                callback_url=callback_url,
                request_options=request_options,
            )
            ingest, progress = self._monitor_batch(ingest, progress, pbar)

        if progress > 0:
            pbar.update(progress)


class AsyncGroundX(AsyncGroundXBase):
    async def load_extraction_definition(
        self,
        *,
        workflow_id: typing.Any = OMIT,
        path: typing.Any = OMIT,
        yaml_text: typing.Any = OMIT,
        mapping: typing.Any = OMIT,
        prepared: typing.Any = OMIT,
        mapping_kind: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Any:
        """
        Load an extraction definition from YAML/prepared input or an existing workflow ID.

        Parameters
        ----------
        workflow_id : typing.Any
            Existing GroundX workflow ID to load.
        path : typing.Any
            Path to an authored extraction YAML file.
        yaml_text : typing.Any
            Authored extraction YAML as a string.
        mapping : typing.Any
            Authored extraction YAML as a mapping, or an existing workflow
            extract mapping when `mapping_kind="workflow_extract"` is set.
        prepared : typing.Any
            A `PreparedExtractionYaml` returned by `prepare_extraction_yaml`.
        mapping_kind : typing.Optional[str]
            Use `"workflow_extract"` only when `mapping` is an existing workflow
            extract payload.
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration forwarded to the generated workflow
            client. Valid only with `workflow_id`.

        Returns
        -------
        typing.Any
            An `ExtractionDefinition`.

        Examples
        --------
        >>> definition = await client.load_extraction_definition(path="statement.yaml")
        >>> existing = await client.load_extraction_definition(workflow_id="workflow-id")

        Notes
        -----
        When `workflow_id` is provided, it takes precedence over YAML/prepared
        inputs. Otherwise pass exactly one of `path`, `yaml_text`, `mapping`, or
        `prepared`.
        """
        selected = _select_extraction_definition_loader_source(
            workflow_id=workflow_id,
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
            request_options=request_options,
        )
        if selected == "workflow_id":
            return await self.load_extraction_definition_from_workflow(
                typing.cast(str, workflow_id),
                request_options=request_options,
            )
        return await self.load_extraction_definition_from_yaml(
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
        )

    async def load_extraction_definition_from_yaml(
        self,
        *,
        path: typing.Any = OMIT,
        yaml_text: typing.Any = OMIT,
        mapping: typing.Any = OMIT,
        prepared: typing.Any = OMIT,
        mapping_kind: typing.Optional[str] = None,
    ) -> typing.Any:
        """
        Load an extraction definition from a YAML path, YAML text, mapping, or prepared object.

        Parameters
        ----------
        path : typing.Any
            Path to an authored extraction YAML file.
        yaml_text : typing.Any
            Authored extraction YAML as a string.
        mapping : typing.Any
            Authored extraction YAML as a mapping, or an existing workflow
            extract mapping when `mapping_kind="workflow_extract"` is set.
        prepared : typing.Any
            A `PreparedExtractionYaml` returned by `prepare_extraction_yaml`.
        mapping_kind : typing.Optional[str]
            Use `"workflow_extract"` only when `mapping` is an existing workflow
            extract payload.

        Returns
        -------
        typing.Any
            An `ExtractionDefinition`.

        Examples
        --------
        >>> definition = await client.load_extraction_definition_from_yaml(path="statement.yaml")

        Prefer `load_extraction_definition(...)` for new code when the source
        may be either YAML or an existing workflow ID.
        """
        extraction_workflows = _import_extraction_workflows()
        return extraction_workflows.load_extraction_definition_from_yaml(
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
        )

    async def load_extraction_definition_from_workflow(
        self,
        workflow_id: str,
        *,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Any:
        """
        Load an extraction definition from an existing workflow ID.

        Parameters
        ----------
        workflow_id : str
            Existing GroundX workflow ID.
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration forwarded to the generated workflow
            client.

        Returns
        -------
        typing.Any
            An `ExtractionDefinition` loaded from the workflow response.

        Examples
        --------
        >>> definition = await client.load_extraction_definition_from_workflow("workflow-id")

        Prefer `load_extraction_definition(workflow_id=...)` for new code when
        the source may be either YAML or an existing workflow ID.
        """
        extraction_workflows = _import_extraction_workflows()
        response = await self.workflows.get(
            workflow_id,
            request_options=request_options,
        )
        return extraction_workflows.load_extraction_definition_from_workflow_response(
            workflow_id,
            response,
        )

    async def create_extraction_workflow(
        self,
        *,
        definition: typing.Any = OMIT,
        path: typing.Any = OMIT,
        yaml_text: typing.Any = OMIT,
        mapping: typing.Any = OMIT,
        prepared: typing.Any = OMIT,
        mapping_kind: typing.Optional[str] = None,
        name: typing.Optional[str] = None,
        chunk_strategy: typing.Any = OMIT,
        section_strategy: typing.Any = OMIT,
        steps: typing.Any = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Any:
        """
        Create an extraction workflow from a definition or YAML/prepared source.

        Parameters
        ----------
        definition : typing.Any
            An `ExtractionDefinition` returned by an extraction definition
            loader.
        path : typing.Any
            Path to an authored extraction YAML file.
        yaml_text : typing.Any
            Authored extraction YAML as a string.
        mapping : typing.Any
            Authored YAML-shaped mapping, or a workflow extract mapping when
            `mapping_kind="workflow_extract"` is set.
        prepared : typing.Any
            A `PreparedExtractionYaml` returned by `prepare_extraction_yaml`.
        mapping_kind : typing.Optional[str]
            Use `"workflow_extract"` only when `mapping` is an existing workflow
            extract payload.
        name : typing.Optional[str]
            Workflow name. Required for create.
        chunk_strategy : typing.Any
            Optional workflow chunk strategy override.
        section_strategy : typing.Any
            Optional workflow section strategy override.
        steps : typing.Any
            Optional fixed workflow step overlay.
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration forwarded to the generated workflow
            client.

        Returns
        -------
        typing.Any
            The generated workflow create response.

        Examples
        --------
        >>> workflow = await client.create_extraction_workflow(
        ...     path="statement.yaml",
        ...     name="statement extraction",
        ... )

        If `definition` is provided, it takes precedence over YAML/prepared
        inputs. Otherwise pass exactly one of `path`, `yaml_text`, `mapping`, or
        `prepared`.
        """
        extraction_workflows = _import_extraction_workflows()
        resolved = extraction_workflows.resolve_extraction_definition_source(
            definition=definition,
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
        )
        kwargs = extraction_workflows.workflow_kwargs_from_extraction_definition(
            resolved,
            name=name,
            require_name=True,
            chunk_strategy=chunk_strategy,
            section_strategy=section_strategy,
            steps=steps,
            request_options=request_options,
        )
        extraction_workflows.ensure_workflow_method_supports_kwargs(
            self.workflows.create,
            kwargs,
        )
        return await self.workflows.create(**kwargs)

    async def update_extraction_workflow(
        self,
        workflow_id: str,
        *,
        definition: typing.Any = OMIT,
        path: typing.Any = OMIT,
        yaml_text: typing.Any = OMIT,
        mapping: typing.Any = OMIT,
        prepared: typing.Any = OMIT,
        mapping_kind: typing.Optional[str] = None,
        name: typing.Any = OMIT,
        chunk_strategy: typing.Any = OMIT,
        section_strategy: typing.Any = OMIT,
        steps: typing.Any = OMIT,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Any:
        """
        Update an extraction workflow from a definition or YAML/prepared source.

        Parameters
        ----------
        workflow_id : str
            Existing workflow ID to update.
        definition : typing.Any
            An `ExtractionDefinition` returned by an extraction definition
            loader.
        path : typing.Any
            Path to an authored extraction YAML file.
        yaml_text : typing.Any
            Authored extraction YAML as a string.
        mapping : typing.Any
            Authored YAML-shaped mapping, or a workflow extract mapping when
            `mapping_kind="workflow_extract"` is set.
        prepared : typing.Any
            A `PreparedExtractionYaml` returned by `prepare_extraction_yaml`.
        mapping_kind : typing.Optional[str]
            Use `"workflow_extract"` only when `mapping` is an existing workflow
            extract payload.
        name : typing.Any
            Optional workflow name to send with the full update payload.
        chunk_strategy : typing.Any
            Optional workflow chunk strategy override.
        section_strategy : typing.Any
            Optional workflow section strategy override.
        steps : typing.Any
            Optional fixed workflow step overlay.
        request_options : typing.Optional[RequestOptions]
            Request-specific configuration forwarded to the generated workflow
            client.

        Returns
        -------
        typing.Any
            The generated workflow update response.

        Examples
        --------
        >>> await client.update_extraction_workflow(
        ...     "workflow-id",
        ...     path="statement.yaml",
        ...     name="statement extraction",
        ... )

        Notes
        -----
        Update sends the full extraction workflow settings, not a patch. If
        `definition` is provided, it takes precedence over YAML/prepared inputs.
        Otherwise pass exactly one of `path`, `yaml_text`, `mapping`, or
        `prepared`.
        """
        extraction_workflows = _import_extraction_workflows()
        resolved = extraction_workflows.resolve_extraction_definition_source(
            definition=definition,
            path=path,
            yaml_text=yaml_text,
            mapping=mapping,
            prepared=prepared,
            mapping_kind=mapping_kind,
        )
        kwargs = extraction_workflows.workflow_kwargs_from_extraction_definition(
            resolved,
            name=name,
            chunk_strategy=chunk_strategy,
            section_strategy=section_strategy,
            steps=steps,
            request_options=request_options,
        )
        extraction_workflows.ensure_workflow_method_supports_kwargs(
            self.workflows.update,
            kwargs,
        )
        return await self.workflows.update(workflow_id, **kwargs)

    async def ingest(
        self,
        *,
        documents: typing.Sequence[Document],
        upload_api: str = "https://api.eyelevel.ai/upload/file",
        callback_url: typing.Optional[str] = None,
        callback_data: typing.Optional[str] = None,
        override_batch_size: typing.Optional[bool] = False,
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

        # an endpoint that will receive processing event updates as POST
        callback_url : typing.Optional[str]

        # a string that is returned, along with processing event updates,
        # to the callback URL.
        callback_data : typing.Optional[str]

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

        max_n = MAX_BATCH_SIZE
        if override_batch_size:
            max_n = 1000

        if len(remote_documents) + len(local_documents) > max_n:
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
                        filter=d.filter,
                        process_level=d.process_level,
                        search_data=d.search_data,
                        source_url=url,
                    )
                )

        return await self.documents.ingest_remote(
            documents=remote_documents,
            callback_url=callback_url,
            callback_data=callback_data,
            request_options=request_options,
        )

    def _upload_file(
        self,
        endpoint: str,
        file_path: Path,
    ) -> str:
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1][1:].lower()
        if f".{file_extension}" in SUFFIX_ALIASES:
            file_extension = SUFFIX_ALIASES[f".{file_extension}"]

        presigned_info = get_presigned_url(endpoint, file_name, file_extension)

        upload_url = presigned_info["URL"]
        hd = presigned_info.get("Header", {})
        method = presigned_info.get("Method", "PUT").upper()

        headers: typing.Dict[str, typing.Any] = {}
        for key, value in hd.items():
            if isinstance(value, list):
                headers[key.upper()] = value[0]

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
            raise Exception(f"Upload failed: {upload_response.status_code} - {upload_response.text}")

        if "GX-HOSTED-URL" in headers:
            return headers["GX-HOSTED-URL"]

        return strip_query_params(upload_url)
