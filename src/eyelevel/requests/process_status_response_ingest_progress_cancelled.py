# This file was auto-generated by Fern from our API Definition.

import typing_extensions
import typing_extensions
import typing
from .document_detail import DocumentDetailParams


class ProcessStatusResponseIngestProgressCancelledParams(typing_extensions.TypedDict):
    documents: typing_extensions.NotRequired[typing.Sequence[DocumentDetailParams]]
    total: typing_extensions.NotRequired[int]
