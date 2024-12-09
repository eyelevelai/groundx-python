# do not import all endpoints into this module because that uses a lot of memory and stack frames
# if you need the ability to import all endpoints from this module, import them with
# from groundx.paths.v1_ingest_documents import Api

from groundx.legacy.paths import PathValues

path = PathValues.V1_INGEST_DOCUMENTS
