import importlib
import typing

if typing.TYPE_CHECKING:
    from .manager import PromptManager
    from .object_store import ObjectStore
    from .source import Source
    from .utility import FinalFieldPath, PreparedExtractionYaml, prepare_extraction_yaml

__all__ = [
    "FinalFieldPath",
    "ObjectStore",
    "PreparedExtractionYaml",
    "PromptManager",
    "Source",
    "prepare_extraction_yaml",
]

_EXPORT_MODULES = {
    "FinalFieldPath": ".utility",
    "ObjectStore": ".object_store",
    "PreparedExtractionYaml": ".utility",
    "PromptManager": ".manager",
    "Source": ".source",
    "prepare_extraction_yaml": ".utility",
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
