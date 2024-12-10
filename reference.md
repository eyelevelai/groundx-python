# Reference
## Documents
<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">list</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

lookup all documents across all resources which are currently on GroundX

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
client.documents.list()

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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">document_ingest</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Ingest documents hosted on public URLs or a local file system for ingestion into a GroundX bucket.

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
from groundx import GroundX, IngestDocument

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.documents.document_ingest(
    documents=[
        IngestDocument(
            bucket_id=1234,
            file_name="my_file.txt",
            file_path="https://my.source.url.com/file.txt",
            file_type="txt",
            search_data={"key": "value"},
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

**documents:** `typing.Sequence[IngestDocument]` 
    
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
client.documents.delete()

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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">ingest_remote</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Ingest documents hosted on public URLs to a GroundX bucket.

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
            file_name="my_file.txt",
            file_type="txt",
            search_data={"key": "value"},
            source_url="https://my.source.url.com/file.txt",
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

Upload documents hosted on a local file system for ingestion into a GroundX bucket.

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
from groundx import GroundX, IngestLocalDocument

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.documents.ingest_local(
    documents=[
        IngestLocalDocument(
            bucket_id=1234,
            file_data="binary data",
            file_name="my_file.txt",
            file_type="txt",
            search_data={"key": "value"},
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

**documents:** `typing.Optional[typing.List[IngestLocalDocument]]` 
    
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
from groundx import CrawlWebsiteSource, GroundX

client = GroundX(
    api_key="YOUR_API_KEY",
)
client.documents.crawl_website(
    websites=[
        CrawlWebsiteSource(
            bucket_id=1234,
            cap=100,
            depth=3,
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

**websites:** `typing.Sequence[CrawlWebsiteSource]` 
    
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

<details><summary><code>client.documents.<a href="src/groundx/documents/client.py">lookup</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

lookup the document(s) associated with a processId, bucketId, groupId, or projectId.

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

**id:** `int` — a processId, bucketId, groupId, or projectId
    
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

The result of this query is typically used in one of two ways; result['search']['text'] can be used to provide context to a language model, facilitating RAG, or result['search']['results'] can be used to observe chunks of text which are relevant to the query, facilitating citation.

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
    next_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
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

**id:** `SearchContentRequestId` — The bucketId, groupId, projectId, or documentId to be searched. The document or documents within the specified container will be compared to the query, and relevant information will be extracted.
    
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

The result of this query is typically used in one of two ways; result['search']['text'] can be used to provide context to a language model, facilitating RAG, or result['search']['results'] can be used to observe chunks of text which are relevant to the query, facilitating citation.

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
    next_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
client.buckets.list()

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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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
client.groups.list()

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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

Interact with the "Request Body" below to explore the arguments of this function. Enter your GroundX API key to send a request directly from this web page. Select your language of choice to structure a code snippet based on your specified arguments.
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

