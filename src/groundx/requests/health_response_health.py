# This file was auto-generated by Fern from our API Definition.

import typing_extensions
import typing
from .health_service import HealthServiceParams


class HealthResponseHealthParams(typing_extensions.TypedDict):
    services: typing.Sequence[HealthServiceParams]