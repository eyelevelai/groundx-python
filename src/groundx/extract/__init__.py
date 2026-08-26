import importlib
import typing

if typing.TYPE_CHECKING:
    from .agents import AgentCode, AgentTool
    from .classes import (
        AgentRequest,
        Document,
        DocumentRequest,
        Element,
        ExtractedField,
        GroundXDocument,
        Group,
        ProcessResponse,
        Prompt,
        TestChunk,
        TestDocumentPage,
        TestField,
        TestXRay,
        XRayDocument,
    )
    from .comparison import match_key, values_match
    from .custom_outputs import (
        CustomOutputDiagnostic,
        CustomOutputReassemblyResult,
        CustomOutputScalarCandidate,
        CustomOutputScalarCandidateSet,
        CustomOutputSourceProvenance,
        RelationshipParentSelection,
        reassemble_custom_outputs,
        reassemble_custom_outputs_from_xray,
        select_relationship_parent,
    )
    from .prompt import (
        FinalFieldPath,
        ObjectStore,
        PreparedExtractionYaml,
        PromptManager,
        Source,
        prepare_extraction_yaml,
    )
    from .services import Logger, RateLimit, SheetsClient, Status, Upload
    from .settings import (
        AgentSettings,
        ContainerSettings,
        ContainerUploadSettings,
        GroundXSettings,
    )
    from .workflows import ExtractionDefinition


__all__ = [
    "AgentCode",
    "AgentRequest",
    "AgentSettings",
    "AgentTool",
    "ContainerSettings",
    "ContainerUploadSettings",
    "CustomOutputDiagnostic",
    "CustomOutputReassemblyResult",
    "CustomOutputScalarCandidate",
    "CustomOutputScalarCandidateSet",
    "CustomOutputSourceProvenance",
    "Document",
    "DocumentRequest",
    "Element",
    "ExtractionDefinition",
    "ExtractedField",
    "FinalFieldPath",
    "GroundXDocument",
    "GroundXSettings",
    "Group",
    "Logger",
    "match_key",
    "ObjectStore",
    "PreparedExtractionYaml",
    "ProcessResponse",
    "Prompt",
    "PromptManager",
    "RateLimit",
    "RelationshipParentSelection",
    "SheetsClient",
    "Source",
    "Status",
    "TestChunk",
    "TestDocumentPage",
    "TestField",
    "TestXRay",
    "Upload",
    "values_match",
    "XRayDocument",
    "prepare_extraction_yaml",
    "reassemble_custom_outputs",
    "reassemble_custom_outputs_from_xray",
    "select_relationship_parent",
]

_EXPORT_MODULES = {
    "AgentCode": ".agents",
    "AgentRequest": ".classes",
    "AgentSettings": ".settings",
    "AgentTool": ".agents",
    "ContainerSettings": ".settings",
    "ContainerUploadSettings": ".settings",
    "CustomOutputDiagnostic": ".custom_outputs",
    "CustomOutputReassemblyResult": ".custom_outputs",
    "CustomOutputScalarCandidate": ".custom_outputs",
    "CustomOutputScalarCandidateSet": ".custom_outputs",
    "CustomOutputSourceProvenance": ".custom_outputs",
    "Document": ".classes",
    "DocumentRequest": ".classes",
    "Element": ".classes",
    "ExtractionDefinition": ".workflows",
    "ExtractedField": ".classes",
    "FinalFieldPath": ".prompt.utility",
    "GroundXDocument": ".classes",
    "GroundXSettings": ".settings",
    "Group": ".classes",
    "Logger": ".services",
    "match_key": ".comparison",
    "ObjectStore": ".prompt.object_store",
    "PreparedExtractionYaml": ".prompt.utility",
    "ProcessResponse": ".classes",
    "Prompt": ".classes",
    "PromptManager": ".prompt.manager",
    "RateLimit": ".services",
    "RelationshipParentSelection": ".custom_outputs",
    "SheetsClient": ".services",
    "Source": ".prompt.source",
    "Status": ".services",
    "TestChunk": ".classes",
    "TestDocumentPage": ".classes",
    "TestField": ".classes",
    "TestXRay": ".classes",
    "Upload": ".services",
    "values_match": ".comparison",
    "XRayDocument": ".classes",
    "prepare_extraction_yaml": ".prompt.utility",
    "reassemble_custom_outputs": ".custom_outputs",
    "reassemble_custom_outputs_from_xray": ".custom_outputs",
    "select_relationship_parent": ".custom_outputs",
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
