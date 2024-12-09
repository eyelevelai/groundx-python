# coding: utf-8
"""
    GroundX APIs

    RAG Made Simple, Secure and Hallucination Free

    The version of the OpenAPI document: 1.3.26
    Contact: support@eyelevel.ai
    Created by: https://www.eyelevel.ai/
"""

from groundx.legacy.paths.v1_ingest_documents_website.post import CrawlWebsite
from groundx.legacy.paths.v1_ingest_documents.delete import Delete
from groundx.legacy.paths.v1_ingest_document_document_id.delete import Delete1
from groundx.legacy.paths.v1_ingest_document_document_id.get import Get
from groundx.legacy.paths.v1_ingest_process_id.get import GetProcessingStatusById
from groundx.legacy.paths.v1_ingest_documents_local.post import IngestLocal
from groundx.legacy.paths.v1_ingest_documents_remote.post import IngestRemote
from groundx.legacy.paths.v1_ingest_documents.get import List
from groundx.legacy.paths.v1_ingest_documents_id.get import Lookup


class DocumentsApiGenerated(
    CrawlWebsite,
    Delete,
    Delete1,
    Get,
    GetProcessingStatusById,
    IngestLocal,
    IngestRemote,
    List,
    Lookup,
):
    """NOTE:
    This class is auto generated by Konfig (https://konfigthis.com)
    """

    pass
