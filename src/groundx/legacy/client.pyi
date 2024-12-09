# coding: utf-8
"""
    GroundX APIs

    RAG Made Simple, Secure and Hallucination Free

    The version of the OpenAPI document: 1.3.26
    Contact: support@eyelevel.ai
    Created by: https://www.eyelevel.ai/
"""

import typing
import inspect
from datetime import date, datetime
from groundx.legacy.client_custom import ClientCustom
from groundx.legacy.configuration import Configuration
from groundx.legacy.api_client import ApiClient
from groundx.legacy.type_util import copy_signature
from groundx.legacy.apis.tags.buckets_api import BucketsApi
from groundx.legacy.apis.tags.customer_api import CustomerApi
from groundx.legacy.apis.tags.documents_api import DocumentsApi
from groundx.legacy.apis.tags.groups_api import GroupsApi
from groundx.legacy.apis.tags.health_api import HealthApi
from groundx.legacy.apis.tags.search_api import SearchApi

class Groundx(ClientCustom):
    def __init__(
        self, configuration: typing.Union[Configuration, None] = None, **kwargs
    ):
        super().__init__(configuration, **kwargs)
        if len(kwargs) > 0:
            configuration = Configuration(**kwargs)
        if configuration is None:
            raise Exception("configuration is required")
        api_client = ApiClient(configuration)
        self.buckets: BucketsApi = BucketsApi(api_client)
        self.customer: CustomerApi = CustomerApi(api_client)
        self.documents: DocumentsApi = DocumentsApi(api_client)
        self.groups: GroupsApi = GroupsApi(api_client)
        self.health: HealthApi = HealthApi(api_client)
        self.search: SearchApi = SearchApi(api_client)
