"""Public test helpers re-exported as part of the `groundx.extract` API.

These functions and classes construct extract objects with simplified
arguments for downstream test code. They are re-exported from
`groundx.extract` and `groundx.extract.classes`.

Previously these lived alongside actual unit tests in `test_field.py` and
`test_groundx.py`. They were separated to make the file-by-file boundary
between "code shipped to users" and "tests run in CI" unambiguous.

Each `Test*` class carries `__test__ = False` so pytest doesn't try to
collect them as `unittest.TestCase` classes despite the `Test*` prefix.
"""

import typing

from .field import ExtractedField
from .prompt import Prompt

__all__ = [
    "TestChunk",
    "TestDocumentPage",
    "TestField",
    "TestXRay",
]


def TestField(
    name: str,
    value: typing.Union[str, float, typing.List[typing.Any]],
    conflicts: typing.Optional[typing.List[typing.Any]] = None,
) -> ExtractedField:
    if conflicts is None:
        conflicts = []
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
    __test__ = False

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
        chunks: typing.Optional[typing.List[TestChunk]] = None,
        document_pages: typing.Optional[typing.List[str]] = None,
    ):
        self.chunks = chunks if chunks is not None else []
        self.documentPages: typing.List[TestDocumentPage] = []
        if document_pages is not None:
            for p in document_pages:
                self.documentPages.append(TestDocumentPage(p))
        self.sourceUrl = source_url
