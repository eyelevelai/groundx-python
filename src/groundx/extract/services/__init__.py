import importlib
import typing

if typing.TYPE_CHECKING:
    from .logger import Logger
    from .ratelimit import RateLimit
    from .sheets_client import SheetsClient
    from .status import Status
    from .upload import Upload

__all__ = [
    "Logger",
    "RateLimit",
    "SheetsClient",
    "Status",
    "Upload",
]

_EXPORT_MODULES = {
    "Logger": ".logger",
    "RateLimit": ".ratelimit",
    "SheetsClient": ".sheets_client",
    "Status": ".status",
    "Upload": ".upload",
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
