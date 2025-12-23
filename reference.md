# Reference
## Documents
<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">copy</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

copy documents from one bucket to another
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**document_ids:** `typing.Optional[typing.Sequence[str]]` — The document IDs of the files you wish to copy.
    
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">ingest_remote</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**documents:** `typing.Sequence[IngestRemoteDocument]` 
    
</dd>
</dl>

<dl>
<dd>

**callback_url:** `typing.Optional[str]` — An endpoint that will receive processing event updates as POST.
    
</dd>
</dl>

<dl>
<dd>

**callback_data:** `typing.Optional[str]` — A string that is returned, along with processing event updates, to the callback URL.
    
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">ingest_local</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">crawl_website</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Upload the content of a publicly accessible website for ingestion into a GroundX bucket. This is done by following links within a specified URL, recursively, up to a specified depth or number of pages.

Note1: This endpoint is currently not supported for on-prem deployments. 
Note2: The `source_url` must include the protocol, http:// or https://.

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
from groundx import GroundX, WebsiteSource

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.documents.crawl_website(
    websites=[
        WebsiteSource(
            bucket_id=1234,
            cap=10,
            depth=2,
            search_data={"key": "value"},
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

**websites:** `typing.Sequence[WebsiteSource]` 
    
</dd>
</dl>

<dl>
<dd>

**callback_url:** `typing.Optional[str]` — The URL that will receive processing event updates.
    
</dd>
</dl>

<dl>
<dd>

**callback_data:** `typing.Optional[str]` — A string that is returned, along with processing event updates, to the callback URL.
    
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">list</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**filter:** `typing.Optional[str]` — Only documents with names that contain the filter string will be returned in the results.
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[Sort]` — The document attribute that will be used to sort the results.
    
</dd>
</dl>

<dl>
<dd>

**sort_order:** `typing.Optional[SortOrder]` — The order in which to sort the results. A value for sort must also be set.
    
</dd>
</dl>

<dl>
<dd>

**status:** `typing.Optional[ProcessingStatus]` — A status filter on the get documents query. If this value is set, then only documents with this status will be returned in the results.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — A token for pagination. If the number of documents for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n documents.
    
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">delete</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.documents.delete(
    document_ids="123e4567-e89b-12d3-a456-426614174000,9f7c11a6-24b8-4d52-a9f3-90a7e70a9e49",
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">get_processing_status_by_id</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">cancel_process</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">lookup</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**filter:** `typing.Optional[str]` — Only documents with names that contain the filter string will be returned in the results.
    
</dd>
</dl>

<dl>
<dd>

**sort:** `typing.Optional[Sort]` — The document attribute that will be used to sort the results.
    
</dd>
</dl>

<dl>
<dd>

**sort_order:** `typing.Optional[SortOrder]` — The order in which to sort the results. A value for sort must also be set.
    
</dd>
</dl>

<dl>
<dd>

**status:** `typing.Optional[ProcessingStatus]` — A status filter on the get documents query. If this value is set, then only documents with this status will be returned in the results.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — A token for pagination. If the number of documents for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n documents.
    
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">get</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">delete_by_id</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">get_extract</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">get_processes</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**status:** `typing.Optional[ProcessingStatus]` — A status filter on the processing status. If this value is set, then only processes with this status will be returned in the results.
    
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
<details><summary><code>client.search.<a href="src/groundx/search/client.py">content</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Search documents on GroundX for the most relevant information to a given query.
The result of this query is typically used in one of two ways; `result.search.text` can be used to provide context to a language model, facilitating RAG, or `result.search.results` can be used to observe chunks of text which are relevant to the query, facilitating citation.
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**query:** `str` — The search query to be used to find relevant documentation.
    
</dd>
</dl>

<dl>
<dd>

**n:** `typing.Optional[int]` — The maximum number of returned search results. Accepts 1-100 with a default of 20.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — A token for pagination. If the number of search results for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n search results.
    
</dd>
</dl>

<dl>
<dd>

**verbosity:** `typing.Optional[int]` — The amount of data returned with each search result. 0 == no search results, only the recommended context. 1 == search results but no searchData. 2 == search results and searchData.
    
</dd>
</dl>

<dl>
<dd>

**filter:** `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]` — A dictionary of key-value pairs that can be used to pre-filter documents prior to a search.
    
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

<details><summary><code>client.search.<a href="src/groundx/search/client.py">documents</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Search documents on GroundX for the most relevant information to a given query by documentId(s).
The result of this query is typically used in one of two ways; `result.search.text` can be used to provide context to a language model, facilitating RAG, or `result.search.results` can be used to observe chunks of text which are relevant to the query, facilitating citation.
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

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.search.documents(
    n=1,
    next_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
    verbosity=1,
    query="my search query",
    document_ids=["docUUID1", "docUUID2"],
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

**query:** `str` — The search query to be used to find relevant documentation.
    
</dd>
</dl>

<dl>
<dd>

**document_ids:** `typing.Sequence[str]` — An array of unique documentIds to be searched.
    
</dd>
</dl>

<dl>
<dd>

**n:** `typing.Optional[int]` — The maximum number of returned search results. Accepts 1-100 with a default of 20.
    
</dd>
</dl>

<dl>
<dd>

**next_token:** `typing.Optional[str]` — A token for pagination. If the number of search results for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n search results.
    
</dd>
</dl>

<dl>
<dd>

**verbosity:** `typing.Optional[int]` — The amount of data returned with each search result. 0 == no search results, only the recommended context. 1 == search results but no searchData. 2 == search results and searchData.
    
</dd>
</dl>

<dl>
<dd>

**filter:** `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]` — A dictionary of key-value pairs that can be used to pre-filter documents prior to a search.
    
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
<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">list</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**next_token:** `typing.Optional[str]` — A token for pagination. If the number of buckets for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n buckets.
    
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

<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">create</a>(...)</code></summary>
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
from groundx import GroundX

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.buckets.create(
    name="your_bucket_name",
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

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">get</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Rename a bucket.
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

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.buckets.update(
    bucket_id=1,
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

**new_name:** `str` — The new name of the bucket being renamed.
    
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

<details><summary><code>client.buckets.<a href="src/groundx/buckets/client.py">delete</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

## Groups
<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">list</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**next_token:** `typing.Optional[str]` — A token for pagination. If the number of groups for a given query is larger than n, the response will include a "nextToken" value. That token can be included in this field to retrieve the next batch of n groups.
    
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

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">create</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">get</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">update</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.groups.update(
    group_id=1,
    new_name="your_group_name",
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

**new_name:** `str` — The new name of the group being renamed.
    
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

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">delete</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">add_bucket</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.groups.<a href="src/groundx/groups/client.py">remove_bucket</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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
<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">list</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Get all workflows associated with the API key.
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">create</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**chunk_strategy:** `typing.Optional[WorkflowRequestChunkStrategy]` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[str]` — The name of the workflow being created.
    
</dd>
</dl>

<dl>
<dd>

**extract:** `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]` — Extract agent definitions.
    
</dd>
</dl>

<dl>
<dd>

**steps:** `typing.Optional[WorkflowSteps]` 
    
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

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">get_account</a>()</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">add_to_account</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**workflow_id:** `str` — The id of the workflow that is being applied.
    
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

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">remove_from_account</a>()</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">add_to_id</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**workflow_id:** `str` — The id of the workflow that is being applied.
    
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

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">remove_from_id</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">get</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.workflows.get(
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

**id:** `WorkflowsGetRequestId` — The id of the group, bucket, or workflow to look up.
    
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

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">update</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Update an existing workflow.
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

**chunk_strategy:** `typing.Optional[WorkflowRequestChunkStrategy]` 
    
</dd>
</dl>

<dl>
<dd>

**name:** `typing.Optional[str]` — The name of the workflow being created.
    
</dd>
</dl>

<dl>
<dd>

**extract:** `typing.Optional[typing.Dict[str, typing.Optional[typing.Any]]]` — Extract agent definitions.
    
</dd>
</dl>

<dl>
<dd>

**steps:** `typing.Optional[WorkflowSteps]` 
    
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

<details><summary><code>client.workflows.<a href="src/groundx/workflows/client.py">delete</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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
<details><summary><code>client.customer.<a href="src/groundx/customer/client.py">get</a>()</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

## Health
<details><summary><code>client.health.<a href="src/groundx/health/client.py">list</a>()</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

<details><summary><code>client.health.<a href="src/groundx/health/client.py">get</a>(...)</code></summary>
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

client = GroundX(
    api_key="YOUR_API_KEY",
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

