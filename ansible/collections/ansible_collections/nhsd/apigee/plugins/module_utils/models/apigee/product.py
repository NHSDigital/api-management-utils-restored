import json
from typing import Union, Literal, List, Dict, Any, Type

from pydantic import (
    BaseModel,
    ValidationError,
    constr,
    conint,
    conlist,
    validator,
    root_validator,
)

from ansible_collections.nhsd.apigee.plugins.module_utils.models.apigee.rate_limiting_config import (
    RateLimitingConfig,
)

LITERAL_APIGEE_ENVIRONMENTS = Literal[
    "internal-dev",
    "internal-dev-sandbox",
    "internal-qa",
    "internal-qa-sandbox",
    "ref",
    "dev",
    "sandbox",
    "int",
    "prod",
]
MANUAL_APPROVAL_EXCEPTIONS = ["canary-api-prod"]


class ApigeeProductAttributeRateLimiting(BaseModel):
    name: Literal["ratelimiting"]
    value: Union[Dict[str, RateLimitingConfig], str]

    @validator("value")
    def validate_ratelimiting(
        cls, ratelimiting: Union[Dict[str, RateLimitingConfig], str]
    ) -> str:
        """
        Apigee API requires a string.  We decode it as JSON in the
        shared flow.

        So if pydantic has happily parsed this into a
        Dict[str,RateLimitingConfig], then json dump it.

        Otherwise, if we've gotten a string (e.g. by calling the
        Apigee API) check the schema is valid using the pydantic
        models.

        Running strings through a JSON parser will also 'normalize'
        the JSON string, so whitespace and key order doesn't matter
        for diffs.
        """
        error_msg = f"Malformed 'ratelimiting' attribute: {ratelimiting}"

        if isinstance(ratelimiting, str):
            # If we have a string, run it through Pydantic by hand.
            try:
                ratelimiting_dict = json.loads(ratelimiting)
                for key, value in ratelimiting_dict.items():
                    ratelimiting_dict[key] = RateLimitingConfig(**value)
                ratelimiting = ratelimiting_dict
            except (ValidationError, json.JSONDecodeError):
                raise ValueError(error_msg)

        # Apigee enforces these must be strings, so do a nicely sorted
        # JSON dump.
        ratelimiting_dict = {}
        for proxy_name, config in ratelimiting.items():
            ratelimiting_dict[proxy_name] = config.dict()
            ratelimiting = json.dumps(ratelimiting_dict, sort_keys=True)
        return ratelimiting


class ApigeeProductAttributeAccess(BaseModel):
    name: Literal["access"]
    value: Literal["public", "private"]


class ApigeeProductAttributeRateLimit(BaseModel):
    name: Literal["ratelimit"]
    value: constr(regex=r"^[0-9]+(ps|pm)$")


def _literal_name(class_):
    # This accesses the 'attribute_name' from
    # class class_:
    #   name: Literal['attribute_name']
    return class_.__fields__["name"].type_.__args__[0]


# This ensures that a generic ApigeeProductAttribute can't be
# constructed from a more specific one that fails valiation.  Sadly
# the pydantic error message is a mess, e.g. if you pass in
# 'ratelimiting' with invalid JSON, the error messages will tell you
# you failed validation for all our customized ApigeeProductAttribute
# types.
PRODUCT_ATTRIBUTE_REGEX = (
    "^(?!("
    + "|".join(
        _literal_name(c)
        for c in [
            ApigeeProductAttributeAccess,
            ApigeeProductAttributeRateLimit,
            ApigeeProductAttributeRateLimiting,
        ]
    )
    + ")$)"
)


class ApigeeProductAttribute(BaseModel):
    name: constr(regex=PRODUCT_ATTRIBUTE_REGEX)
    value: str


def _count_cls(items: List[Any], cls: Type):
    return sum(isinstance(item, cls) for item in items)


class ApigeeProduct(BaseModel):
    name: str
    approvalType: Literal["auto", "manual"] = "manual"
    attributes: List[
        Union[
            ApigeeProductAttributeAccess,
            ApigeeProductAttributeRateLimit,
            ApigeeProductAttributeRateLimiting,
            ApigeeProductAttribute,
        ],
    ] = [{"name": "access", "value": "private"}]
    description: str = None
    displayName: str = None

    # Note: This value is manually inserted by apigee_environment
    # object that contains this product. So if you do not provide a
    # value in the manifest file it is still populated.
    environments: conlist(
        item_type=LITERAL_APIGEE_ENVIRONMENTS, min_items=1, max_items=1
    )
    proxies: List[str] = []
    quota: constr(regex=r"[1-9][0-9]*") = None
    quotaInterval: constr(regex=r"[1-9][0-9]*") = None
    quotaTimeUnit: Literal["minute", "hour"] = None
    scopes: List[str] = []

    class Config:
        extra = "forbid"

    @root_validator
    def override_approval_type_for_prod(cls, values):
        name = values["name"]
        environments = values["environments"]
        if "prod" in environments and name not in MANUAL_APPROVAL_EXCEPTIONS:
            values["approvalType"] = "manual"
        return values

    @validator("environments", "scopes", "proxies", check_fields=False)
    def sorted(cls, v):
        return sorted(v)

    @validator("attributes")
    def validate_attributes(cls, attributes, values):
        attributes = sorted(attributes, key=lambda a: a.name)

        class_min_max = [
            (ApigeeProductAttributeAccess, 1, 1),
            (ApigeeProductAttributeRateLimit, 0, 1),
            (ApigeeProductAttributeRateLimiting, 0, 1),
        ]

        for _class, _min, _max in class_min_max:
            count = _count_cls(attributes, _class)
            if count < _min or count > _max:
                if _min == _max:
                    count_msg = f"exactly {_min}"
                else:
                    count_msg = f"between {_min} and {_max}"
                raise AssertionError(
                    f"Product {values['name']} must contain {count_msg} "
                    + f"'{_literal_name(_class)}' attributes , "
                    + f"your product has {count}."
                )

        return attributes

    @validator("proxies", always=True)
    def ensure_identity_service(cls, proxies, values):
        """
        We never want to deploy products with no proxies, as that
        allows access to absolutely everything in the apigee
        organization.

        This validator will inject the identity-service for the
        environment if the list of proxies is empty.
        """
        if len(proxies) == 0:
            env = values["environments"][0]
            return [f"identity-service-{env}"]
        return proxies

    @validator("displayName", always=True)
    def validate_display_name(cls, displayName, values):
        if not displayName:
            return values["name"]
        return displayName
