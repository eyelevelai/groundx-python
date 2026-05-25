"""Public test helpers re-exported as part of the `groundx.extract` API.

These functions and classes construct extract objects with simplified
arguments for downstream test code. They are re-exported from
`groundx.extract` and `groundx.extract.classes`.

Previously these lived alongside actual unit tests in `test_field.py` and
`test_groundx.py`. They were separated to make the file-by-file boundary
between "code shipped to users" and "tests run in CI" unambiguous.
"""

import typing

from .field import ExtractedField
from .prompt import Prompt


def TestField(
    name: str,
    value: typing.Union[str, float, typing.List[typing.Any]],
    conflicts: typing.List[typing.Any] = [],
) -> ExtractedField:
    return ExtractedField(
        prompt=Prompt(
            attr_name=name.replace("_", " "),
            identifiers=[name],
            instructions=name.replace("_", " "),
        ),
        value=value,
        conflicts=conflicts,
    )


class TestChunk:
    __test__ = False  # tells pytest this isn't a unittest class despite the Test* prefix

    def __init__(self, json_str: str):
        self.sectionSummary = None
        self.suggestedText = json_str


class TestDocumentPage:
    __test__ = False

    def __init__(self, page_url: str):
        self.pageUrl = page_url


class TestXRay:
    __test__ = False

    def __init__(
        self,
        source_url: str,
        chunks: typing.Optional[typing.List[TestChunk]] = [],
        document_pages: typing.Optional[typing.List[str]] = [],
    ):
        self.chunks = chunks
        self.documentPages: typing.List[TestDocumentPage] = []
        if document_pages is not None:
            for p in document_pages:
                self.documentPages.append(TestDocumentPage(p))
        self.sourceUrl = source_url
