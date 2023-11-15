import typing
import pydantic
from ansible_collections.nhsd.apigee.plugins.module_utils.models.apigee.spec import (
    ApigeeSpec,
)
from ansible_collections.nhsd.apigee.plugins.module_utils.models.apigee.product import (
    ApigeeProduct,
    LITERAL_APIGEE_ENVIRONMENTS
)


class ManifestApigeeEnvironment(pydantic.BaseModel):
    name: LITERAL_APIGEE_ENVIRONMENTS
    products: typing.List[ApigeeProduct] = []
    specs: typing.List[ApigeeSpec] = []

    @pydantic.validator("products", "specs")
    def names_unique(cls, values):
        names = [v.name for v in values]
        if len(names) != len(set(names)):
            raise ValueError("Names are not unique")
        return values

    @pydantic.validator("products", pre=True)
    def set_single_environment(cls, products, values):
        """
        Manually set the product environments to match manifest
        environment.
        """
        env = values["name"]
        for i in range(len(products)):
            products[i]["environments"] = [env]
        return products
