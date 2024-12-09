import typing_extensions

from groundx.legacy.apis.tags import TagValues
from groundx.legacy.apis.tags.documents_api import DocumentsApi
from groundx.legacy.apis.tags.search_api import SearchApi
from groundx.legacy.apis.tags.buckets_api import BucketsApi
from groundx.legacy.apis.tags.groups_api import GroupsApi
from groundx.legacy.apis.tags.customer_api import CustomerApi
from groundx.legacy.apis.tags.health_api import HealthApi

TagToApi = typing_extensions.TypedDict(
    "TagToApi",
    {
        TagValues.DOCUMENTS: DocumentsApi,
        TagValues.SEARCH: SearchApi,
        TagValues.BUCKETS: BucketsApi,
        TagValues.GROUPS: GroupsApi,
        TagValues.CUSTOMER: CustomerApi,
        TagValues.HEALTH: HealthApi,
    },
)

tag_to_api = TagToApi(
    {
        TagValues.DOCUMENTS: DocumentsApi,
        TagValues.SEARCH: SearchApi,
        TagValues.BUCKETS: BucketsApi,
        TagValues.GROUPS: GroupsApi,
        TagValues.CUSTOMER: CustomerApi,
        TagValues.HEALTH: HealthApi,
    }
)
