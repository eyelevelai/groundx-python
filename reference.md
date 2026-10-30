# Reference
## Documents
<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">copy</a>(...) -> IngestResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Copy documents from one bucket to another.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.copy(
    to_bucket=1234,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**to_bucket:** `int` — The bucketId of the bucket the file will be copied into.
    
</dd>
</dl>

<dl>
<dd>

**document_ids:** `typing.Optional[typing.List[str]]` — The document IDs of the files you wish to copy.
    
</dd>
</dl>

<dl>
<dd>

**from_bucket:** `typing.Optional[int]` — The bucketId of the bucket you wish to copy ALL files from.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">ingest_remote</a>(...) -> IngestResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Ingest documents hosted on public URLs into a GroundX bucket.

[Supported Document Types and Ingest Capacities](https://docs.eyelevel.ai/documentation/fundamentals/document-types-and-ingest-capacities)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX, IngestRemoteDocument
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.ingest_remote(
    documents=[
        IngestRemoteDocument(
            bucket_id=1234,
            file_name="my_file1.txt",
            file_type="txt",
            source_url="https://my.source.url.com/file1.txt",
        )
    ],
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**documents:** `typing.List[IngestRemoteDocument]` 
    
</dd>
</dl>

<dl>
<dd>

**callback_url:** `typing.Optional[str]` — URL that receives processing updates as POST requests.
    
</dd>
</dl>

<dl>
<dd>

**callback_data:** `typing.Optional[str]` — Custom string included in processing updates sent to the callback URL.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">ingest_local</a>(...) -> IngestResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Upload documents hosted on a local file system into a GroundX bucket.

[Supported Document Types and Ingest Capacities](https://docs.eyelevel.ai/documentation/fundamentals/document-types-and-ingest-capacities)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX, IngestLocalDocument, IngestLocalDocumentMetadata
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.ingest_local(
    request=[
        IngestLocalDocument(
            blob="blob",
            metadata=IngestLocalDocumentMetadata(
                bucket_id=1234,
                file_name="my_file1.txt",
                file_type="txt",
            ),
        )
    ],
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request:** `DocumentLocalIngestRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">crawl_website</a>(...) -> IngestResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Ingest a public website by following links from a starting URL, up to the requested depth or page limit. The source_url must start with http:// or https://. Website crawling is not supported on-prem. [Supported Document Types and Ingest Capacities](https://docs.eyelevel.ai/documentation/fundamentals/document-types-and-ingest-capacities)
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX, WebsiteSource
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.crawl_website(
    websites=[
        WebsiteSource(
            bucket_id=1234,
            cap=10,
            depth=2,
            search_data={
                "key": "value"
            },
            source_url="https://my.website.com",
        )
    ],
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**websites:** `typing.List[WebsiteSource]` 
    
</dd>
</dl>

<dl>
<dd>

**callback_url:** `typing.Optional[str]` — The URL that will receive processing event updates.
    
</dd>
</dl>

<dl>
<dd>

**callback_data:** `typing.Optional[str]` — Custom string included in processing updates sent to the callback URL.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">list</a>(...) -> DocumentListResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

lookup all documents across all resources which are currently on GroundX
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.list(
    n=1,
    filter="filter",
    sort="name",
    sort_order="asc",
    status="queued",
    next_token="nextToken",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**n:** `typing.Optional[int]` — The maximum number of returned documents. Accepts 1-100 with a default of 20.
    
</dd>
</dl>

<dl>
<dd>

**filter:** `typing.Optional[str]` — Return only documents whose names contain this string.
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[Sort]` — The document attribute that will be used to sort the results.
    
</dd>
</dl>

<dl>
<dd>

**sort_order:** `typing.Optional[SortOrder]` — Sort order. Requires sort.
    
</dd>
</dl>

<dl>
<dd>

**status:** `typing.Optional[ProcessingStatus]` — Return only documents with this status.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — Pass nextToken from the previous response to get the next page of up to n documents.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">update</a>(...) -> IngestResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update the attributes of documents that have been uploaded to GroundX.
Policy-bearing updates return 403 when file access is disabled; enabled
temporary failures return 503 with Retry-After.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX, DocumentUpdate
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.update(
    documents=[
        DocumentUpdate(
            document_id="documentId",
        )
    ],
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**documents:** `typing.List[DocumentUpdate]` 
    
</dd>
</dl>

<dl>
<dd>

**callback_url:** `typing.Optional[str]` — URL that receives processing updates as POST requests.
    
</dd>
</dl>

<dl>
<dd>

**callback_data:** `typing.Optional[str]` — Custom string included in processing updates sent to the callback URL.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">delete</a>(...) -> IngestResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete multiple documents hosted on GroundX
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.delete(
    document_ids=[
        "123e4567-e89b-12d3-a456-426614174000,9f7c11a6-24b8-4d52-a9f3-90a7e70a9e49"
    ],
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**document_ids:** `typing.Optional[typing.Union[str, typing.Sequence[str]]]` — A list of documentIds which correspond to documents ingested by GroundX
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">get_processing_status_by_id</a>(...) -> IngestResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the current status of an ingest, initiated with documents.ingest_remote, documents.ingest_local, or documents.crawl_website, by specifying the processId (the processId is included in the response of the documents.ingest functions).
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.get_processing_status_by_id(
    process_id="processId",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**process_id:** `str` — the processId for the ingest process being checked
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">cancel_process</a>(...) -> IngestResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Cancel an ingest process, along with any files that have not been completely ingested.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.cancel_process(
    process_id="processId",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**process_id:** `str` — the processId for the ingest process to be cancelled
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">lookup</a>(...) -> DocumentLookupResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

lookup the document(s) associated with a processId, bucketId, or groupId.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.lookup(
    id=1,
    n=1,
    filter="filter",
    sort="name",
    sort_order="asc",
    status="queued",
    next_token="nextToken",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `int` — a processId, bucketId, or groupId
    
</dd>
</dl>

<dl>
<dd>

**n:** `typing.Optional[int]` — The maximum number of returned documents. Accepts 1-100 with a default of 20.
    
</dd>
</dl>

<dl>
<dd>

**filter:** `typing.Optional[str]` — Return only documents whose names contain this string.
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[Sort]` — The document attribute that will be used to sort the results.
    
</dd>
</dl>

<dl>
<dd>

**sort_order:** `typing.Optional[SortOrder]` — Sort order. Requires sort.
    
</dd>
</dl>

<dl>
<dd>

**status:** `typing.Optional[ProcessingStatus]` — Return only documents with this status.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — Pass nextToken from the previous response to get the next page of up to n documents.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">get</a>(...) -> DocumentResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Look up an existing document by documentId.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.get(
    document_id="documentId",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**document_id:** `str` — The documentId of the document for which GroundX information will be provided.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">delete_by_id</a>(...) -> IngestResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a single document hosted on GroundX
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.delete_by_id(
    document_id="documentId",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**document_id:** `str` — A documentId which correspond to a document ingested by GroundX
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">retry_failed_stage</a>(...) -> RetryFailedStageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Retry a failed HTTP callback using its saved output and settings. No request body is needed. Post-processing and manual retries must be enabled. Active or successfully delivered documents and other failed stages return 409. A 202 response confirms acceptance; get the document to check deliveryStatus. An earlier unconfirmed delivery may already have reached the receiver.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.retry_failed_stage(
    document_id="documentId",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**document_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">get_extract</a>(...) -> DocumentsGetExtractResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Look up extractions for an existing document by documentId.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.get_extract(
    document_id="documentId",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**document_id:** `str` — The documentId of the document for which GroundX extract has extracted information.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">get_xray</a>(...) -> DocumentXray</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Look up X-Ray data for an existing document by documentId.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.get_xray(
    document_id="documentId",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**document_id:** `str` — The documentId of the document for which GroundX created an X-Ray.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">get_processes</a>(...) -> ProcessesStatusResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get a list of ingest process requests, sorted from most recent to least.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.get_processes(
    n=1,
    status="queued",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**n:** `typing.Optional[int]` — The maximum number of returned processes. Accepts 1-100 with a default of 20.
    
</dd>
</dl>

<dl>
<dd>

**status:** `typing.Optional[ProcessingStatus]` — Return only processes with this status.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">file_link</a>(...) -> FileLinkResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a storage-signed download link for a saved asset you own. Anyone with the link can use or forward it until expiresAt. Revoking an API key or changing policy does not cancel issued links. The URL contains no GroundX API key. Returns 404 if file access is disabled, or 503 with Retry-After for temporary file-access failures.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX, AssetSelectorCorrected
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.documents.file_link(
    document_id="11111111-1111-4111-8111-111111111111",
    asset=AssetSelectorCorrected(
        kind="page",
        page_number=1,
        corrected=False,
    ),
    expires_in_seconds=120,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**document_id:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**asset:** `AssetSelector` 
    
</dd>
</dl>

<dl>
<dd>

**expires_in_seconds:** `typing.Optional[int]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Search
<details><summary><code>client.search.<a href="src/groundx/search/client.py">content</a>(...) -> SearchResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Search a bucket, group or document for information relevant to a query. Use result.search.text as context for a language model and result.search.results for matching text and citations.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.search.content(
    id=1,
    n=1,
    next_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
    verbosity=1,
    query="my search query",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `SearchContentRequestId` — The bucketId, groupId, or documentId to be searched. The document or documents within the specified container will be compared to the query, and relevant information will be extracted.
    
</dd>
</dl>

<dl>
<dd>

**query:** `str` — Search query.
    
</dd>
</dl>

<dl>
<dd>

**n:** `typing.Optional[int]` — The maximum number of returned search results. Accepts 1-100 with a default of 20.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — Pass nextToken from the previous response to get the next page of up to n search results.
    
</dd>
</dl>

<dl>
<dd>

**verbosity:** `typing.Optional[int]` — Response detail: 0 returns only recommended context; 1 adds search results without searchData; 2 includes searchData.
    
</dd>
</dl>

<dl>
<dd>

**filter:** `typing.Optional[typing.Dict[str, typing.Any]]` — Key-value metadata used to filter documents before searching.
    
</dd>
</dl>

<dl>
<dd>

**relevance:** `typing.Optional[float]` — The minimum search relevance score required to include the result. By default, this is 10.0.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.search.<a href="src/groundx/search/client.py">documents</a>(...) -> SearchResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Search the specified document IDs for information relevant to a query. Use result.search.text as context for a language model and result.search.results for matching text and citations.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.search.documents(
    n=1,
    next_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
    verbosity=1,
    query="my search query",
    document_ids=[
        "docUUID1",
        "docUUID2"
    ],
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**query:** `str` — Search query.
    
</dd>
</dl>

<dl>
<dd>

**document_ids:** `typing.List[str]` — An array of unique documentIds to be searched.
    
</dd>
</dl>

<dl>
<dd>

**n:** `typing.Optional[int]` — The maximum number of returned search results. Accepts 1-100 with a default of 20.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — Pass nextToken from the previous response to get the next page of up to n search results.
    
</dd>
</dl>

<dl>
<dd>

**verbosity:** `typing.Optional[int]` — Response detail: 0 returns only recommended context; 1 adds search results without searchData; 2 includes searchData.
    
</dd>
</dl>

<dl>
<dd>

**filter:** `typing.Optional[typing.Dict[str, typing.Any]]` — Key-value metadata used to filter documents before searching.
    
</dd>
</dl>

<dl>
<dd>

**relevance:** `typing.Optional[float]` — The minimum search relevance score required to include the result. By default, this is 10.0.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Buckets
<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">list</a>(...) -> BucketListResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List all buckets within your GroundX account
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.buckets.list(
    n=1,
    next_token="nextToken",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**n:** `typing.Optional[int]` — The maximum number of returned buckets. Accepts 1-100 with a default of 20.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — Pass nextToken from the previous response to get the next page of up to n buckets.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">create</a>(...) -> BucketResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new bucket.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX, FileAccessPolicy
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.buckets.create(
    name="private-documents",
    file_access=FileAccessPolicy(
        mode="protected",
        url_ttl_seconds=300,
    ),
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**prompt:** `typing.Optional[str]` — Optional prompt text.
    
</dd>
</dl>

<dl>
<dd>

**file_access:** `typing.Optional[FileAccessPolicy]` — Initial settings for this resource. Omit or send null to inherit. Explicit settings take priority over the same account or bucket settings; omitted fields use broader values. Use private staging before uploading a protected file, even in a public bucket. Returns 403 if file access is disabled.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">get</a>(...) -> BucketResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Look up a specific bucket by its bucketId.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.buckets.get(
    bucket_id=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**bucket_id:** `int` — The bucketId of the bucket to look up.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">update</a>(...) -> BucketUpdateResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Rename a bucket or replace its file-access policy. Policy-bearing updates return 403 when file access is disabled; enabled temporary failures return 503 with Retry-After.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.buckets.update(
    bucket_id=7,
    new_name="your_bucket_name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**bucket_id:** `int` — The bucketId of the bucket being updated.
    
</dd>
</dl>

<dl>
<dd>

**prompt:** `typing.Optional[str]` — Optional prompt text.
    
</dd>
</dl>

<dl>
<dd>

**new_name:** `typing.Optional[str]` — The new name of the bucket being renamed.
    
</dd>
</dl>

<dl>
<dd>

**file_access:** `typing.Optional[FileAccessPolicy]` 
    
</dd>
</dl>

<dl>
<dd>

**file_access_revision:** `typing.Optional[int]` — Legacy compatibility field. Not required or checked when changing file access.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">delete</a>(...) -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a bucket.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.buckets.delete(
    bucket_id=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**bucket_id:** `int` — The bucketId of the bucket being deleted.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">file_upload</a>(...) -> FileUploadResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Return a storage-signed PUT link for a public or protected bucket, valid for at most 900 seconds. Complete PUT before it expires. A private upload reservation also requires ingest submission before that deadline; an unreserved public source remains ingestible after PUT expiry. Available even when file-access protection is disabled. Uses this deployment and its configured storage. Include the requested per-file fileAccess policy so it is checked before upload; non-null policies return 403 when protection is disabled. Returns 503 with Retry-After for temporary verification failures.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.buckets.file_upload(
    bucket_id=1234,
    file_name="invoice.pdf",
    file_type="pdf",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**bucket_id:** `int` 
    
</dd>
</dl>

<dl>
<dd>

**file_name:** `str` 
    
</dd>
</dl>

<dl>
<dd>

**file_type:** `DocumentType` 
    
</dd>
</dl>

<dl>
<dd>

**file_access:** `typing.Optional[FileAccessPolicy]` — Requested initial file policy, also sent during ingest. Omit or send null to inherit. Validated before an upload URL is issued. Non-null policies return 403 when file protection is disabled, so a protected upload cannot be staged publicly.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Groups
<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">list</a>(...) -> GroupListResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

list all groups within your GroundX account.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.groups.list(
    n=1,
    next_token="nextToken",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**n:** `typing.Optional[int]` — The maximum number of returned groups. Accepts 1-100 with a default of 20.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — Pass nextToken from the previous response to get the next page of up to n groups.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">create</a>(...) -> GroupResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

create a new group, a group being a collection of buckets which can be searched.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.groups.create(
    name="your_group_name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**name:** `str` — The name of the group being created.
    
</dd>
</dl>

<dl>
<dd>

**prompt:** `typing.Optional[str]` — Optional prompt text.
    
</dd>
</dl>

<dl>
<dd>

**bucket_name:** `typing.Optional[str]` — Specify bucketName to automatically create a bucket, by the name specified, and add it to the created group.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">get</a>(...) -> GroupResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

look up a specific group by its groupId.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.groups.get(
    group_id=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**group_id:** `int` — The groupId of the group to look up.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">update</a>(...) -> GroupResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Rename a group
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.groups.update(
    group_id=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**group_id:** `int` — The groupId of the group to update.
    
</dd>
</dl>

<dl>
<dd>

**prompt:** `typing.Optional[str]` — Optional prompt text.
    
</dd>
</dl>

<dl>
<dd>

**new_name:** `typing.Optional[str]` — The new name of the group being renamed.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">delete</a>(...) -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a group.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.groups.delete(
    group_id=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**group_id:** `int` — The groupId of the group to be deleted.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">add_bucket</a>(...) -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Add an existing bucket to an existing group. Buckets and groups can be associated many to many.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.groups.add_bucket(
    group_id=1,
    bucket_id=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**group_id:** `int` — The groupId of the group which the bucket will be added to.
    
</dd>
</dl>

<dl>
<dd>

**bucket_id:** `int` — The bucketId of the bucket being added to the group.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">remove_bucket</a>(...) -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

remove a bucket from a group. Buckets and groups can be associated many to many, this removes one bucket to group association without disturbing others.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.groups.remove_bucket(
    group_id=1,
    bucket_id=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**group_id:** `int` — The groupId of the group which the bucket will be removed from.
    
</dd>
</dl>

<dl>
<dd>

**bucket_id:** `int` — The bucketId of the bucket which will be removed from the group.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Workflows
<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">list</a>() -> WorkflowsResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List workflow IDs, names, update times, and attachments. Use GET /v1/workflow/{id} to get the full workflow.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">create</a>(...) -> WorkflowResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a workflow.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.create()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request:** `WorkflowRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">validate</a>(...) -> WorkflowResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Validate a workflow without saving changes. Accepts the workflow-create request body, including authored YAML in yaml. Returns the compiled workflow or the same structured validation errors as create.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.validate()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request:** `WorkflowRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">get_account</a>() -> WorkflowResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the workflow associated with customer account.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.get_account()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">add_to_account</a>(...) -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Assigns the given workflow to the customer account and is applied by default to all files unless overridden by document or bucket workflows.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.add_to_account(
    workflow_id="workflowId",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request:** `WorkflowApplyRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">remove_from_account</a>() -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Removes the assigned workflow from the customer account.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.remove_from_account()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">add_to_id</a>(...) -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Assigns the given workflow to the group or bucket and is applied by default to all files unless overridden by document workflows.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.add_to_id(
    id=1,
    workflow_id="workflowId",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `int` — The id of the group or bucket that the workflow will be assigned to.
    
</dd>
</dl>

<dl>
<dd>

**request:** `WorkflowApplyRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">remove_from_id</a>(...) -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Removes the assigned workflow from the customer account.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.remove_from_id(
    id=1,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `int` — The id of the group or bucket that the workflow will removed from.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">get</a>(...) -> WorkflowResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

look up a specific workflow by groupId, bucketId, or workflowId.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.get(
    id=1,
    format="json",
    metadata_only=True,
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `WorkflowsGetRequestId` — The id of the group, bucket, or workflow to look up.
    
</dd>
</dl>

<dl>
<dd>

**format:** `typing.Optional[WorkflowsGetRequestFormat]` — Response format. `yaml` returns the stored authored workflow YAML source verbatim (absent for workflows created via compiled JSON).
    
</dd>
</dl>

<dl>
<dd>

**metadata_only:** `typing.Optional[bool]` — When true, return workflow metadata such as workflowId and updatedAt without returning the workflow extract/settings body.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">update</a>(...) -> WorkflowResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Replace an existing workflow's custom settings relative to GroundX defaults. Omitted steps and step settings return to defaults. A null step disables or clears it. For step settings, omit prompt or send prompt: {} to use default prompts; prompt: null removes the prompt group. A name-only request also resets custom processing settings. Include every custom setting you want to keep.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.update(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `str` — The workflowId of the workflow being updated.
    
</dd>
</dl>

<dl>
<dd>

**request:** `WorkflowRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">delete</a>(...) -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete a workflow.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.workflows.delete(
    id="id",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**id:** `str` — The workflowId of the workflow being deleted.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Customer
<details><summary><code>client.customer.<a href="src/groundx/customer/client.py">get</a>() -> CustomerResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get the account information associated with the API key.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.customer.get()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.customer.<a href="src/groundx/customer/client.py">update</a>(...) -> CustomerResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Replace or clear your account's file-access settings. Send only fileAccess; the latest successful update takes effect. Invalid or missing input returns 400; disabled or forbidden access returns 403; ownership or source conflicts return 409. If settings or ownership cannot be verified, returns 503 with Retry-After. After an uncertain outcome, read the applied settings before retrying. Protected stable links require X-API-Key on every read.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX, FileAccessPolicy
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.customer.update(
    file_access=FileAccessPolicy(
        mode="protected",
        url_ttl_seconds=300,
    ),
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**file_access:** `typing.Optional[FileAccessPolicy]` 
    
</dd>
</dl>

<dl>
<dd>

**file_access_revision:** `typing.Optional[int]` — Legacy compatibility field. Not required or checked when changing file access.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.customer.<a href="src/groundx/customer/client.py">get_usage</a>(...) -> CustomerUsageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get usage for the authenticated account over a time period. GroundX selects its subscription and usage meter; do not supply their IDs or a customer ID. startTime is inclusive and endTime is exclusive. Both must be RFC3339 timestamps on minute boundaries and are converted to UTC. endTime cannot be in the future. The window cannot exceed 366 days. usageAsOf identifies the latest usage summary available to GroundX.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment
import datetime

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.customer.get_usage(
    metric="searches",
    start_time=datetime.datetime.fromisoformat("2026-07-15T00:00:00+00:00"),
    end_time=datetime.datetime.fromisoformat("2026-07-29T00:00:00+00:00"),
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**metric:** `CustomerGetUsageRequestMetric` — Supported usage metric to query.
    
</dd>
</dl>

<dl>
<dd>

**start_time:** `datetime.datetime` — Inclusive RFC3339 window start. Must be aligned to a minute boundary.
    
</dd>
</dl>

<dl>
<dd>

**end_time:** `datetime.datetime` — Exclusive RFC3339 window end. Must be aligned to a minute boundary and cannot be in the future.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## ApiKey
<details><summary><code>client.api_key.<a href="src/groundx/api_key/client.py">list</a>() -> ApiKeyResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List all API keys within your GroundX account
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.api_key.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_key.<a href="src/groundx/api_key/client.py">create</a>(...) -> ApiKeyResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Create a new API key.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.api_key.create(
    name="your_apikey_name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request:** `ApiKeyRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_key.<a href="src/groundx/api_key/client.py">update</a>(...) -> ApiKeyResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Rename an API key.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.api_key.update(
    api_key="apiKey",
    name="your_apikey_name",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**api_key:** `str` — The API key being updated.
    
</dd>
</dl>

<dl>
<dd>

**request:** `ApiKeyRequest` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.api_key.<a href="src/groundx/api_key/client.py">delete</a>(...) -> MessageResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Delete an API key.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.api_key.delete(
    api_key="apiKey",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**api_key:** `str` — The API key being deleted.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Health
<details><summary><code>client.health.<a href="src/groundx/health/client.py">list</a>() -> HealthResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

List the current health status of all services. Statuses update every 5 minutes.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.health.list()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.health.<a href="src/groundx/health/client.py">get</a>(...) -> HealthResponse</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Look up the current health status of a specific service. Statuses update every 5 minutes.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from groundx import GroundX
from groundx.environment import GroundXEnvironment

client = GroundX(
    api_key="<value>",
    environment=GroundXEnvironment.DEFAULT,
)

client.health.get(
    service="search",
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**service:** `str` — The name of the service to look up.
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

