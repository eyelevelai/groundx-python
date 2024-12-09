# This file was auto-generated by Fern from our API Definition.

import typing_extensions
import typing_extensions
from .subscription_detail_meters import SubscriptionDetailMetersParams


class SubscriptionDetailParams(typing_extensions.TypedDict):
    """
    Subscription information for the user, including current usage and limits
    """

    meters: typing_extensions.NotRequired[SubscriptionDetailMetersParams]