import importlib
import typing

if typing.TYPE_CHECKING:
    from .agent import AgentRequest
    from .api import ProcessResponse
    from .document import Document, DocumentRequest
    from .element import Element
    from .field import ExtractedField
    from .groundx import GroundXDocument, XRayDocument
    from .group import Group
    from .prompt import Prompt
    from .testing import TestChunk, TestDocumentPage, TestField, TestXRay


__all__ = [
    "AgentRequest",
    "Document",
    "DocumentRequest",
    "Element",
    "ExtractedField",
    "GroundXDocument",
    "Group",
    "ProcessResponse",
    "Prompt",
    "TestChunk",
    "TestDocumentPage",
    "TestField",
    "TestXRay",
    "XRayDocument",
]

_EXPORT_MODULES = {
    "AgentRequest": ".agent",
    "Document": ".document",
    "DocumentRequest": ".document",
    "Element": ".element",
    "ExtractedField": ".field",
    "GroundXDocument": ".groundx",
    "Group": ".group",
    "ProcessResponse": ".api",
    "Prompt": ".prompt",
    "TestChunk": ".testing",
    "TestDocumentPage": ".testing",
    "TestField": ".testing",
    "TestXRay": ".testing",
    "XRayDocument": ".groundx",
}


def __getattr__(name: str) -> typing.Any:
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = importlib.import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> typing.List[str]:
    return sorted(set(globals()) | set(__all__))
