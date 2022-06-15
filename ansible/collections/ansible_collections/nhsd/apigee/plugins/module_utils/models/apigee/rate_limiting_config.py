"""
Pydantic class for the rateliming config JSON, attached to products
and apps to control the ApplyRateLimiting shared flow.
"""
from typing import Literal

from pydantic import BaseModel, conint, constr, Extra


class ExcludeNoneModel(BaseModel):

    """
    Providing default values for ratelimiting here would mean that
    changing defaults required a redeploy for all proxies.

    Therefore we set None as the default value on all
    RateLimitingConfig attributes, and *do not* export them as JSON.

    The platform defaults are used to fill in the missing values
    inside the ApplyRateLimiting shared flow.  This pattern us to
    update the defaults for everyone by just by updating the shared
    flow.
    """
    def dict(self, **kwargs):
        kwargs["exclude_none"] = True
        return super().dict(**kwargs)

    class Config:
        extra=Extra.forbid


class QuotaConfig(ExcludeNoneModel):
    enabled: bool = None
    interval: conint(gt=0) = None
    limit: conint(gt=0) = None
    timeunit: Literal["minute", "hour", "day", "week", "month"] = None


class SpikeArrestConfig(ExcludeNoneModel):
    enabled: bool = None
    ratelimit: constr(regex=r"^[1-9][0-9]*(ps|pm)$") = None


class RateLimitingConfig(ExcludeNoneModel):
    quota: QuotaConfig = None
    spikeArrest: SpikeArrestConfig = None
