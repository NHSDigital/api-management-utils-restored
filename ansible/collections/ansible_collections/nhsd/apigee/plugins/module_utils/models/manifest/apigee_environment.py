import typing
import pydantic
from ansible_collections.nhsd.apigee.plugins.module_utils.models.apigee.apidoc import (
    ApigeeApidoc,
)
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
    api_catalog: typing.List[ApigeeApidoc] = []

    @pydantic.validator("products", "specs")
    def names_unique(cls, values):
        names = [v.name for v in values]
        if len(names) != len(set(names)):
            raise ValueError("Names are not unique")
        return values

    @pydantic.validator("api_catalog")
    def catalog_references(cls, api_catalog, values):
        spec_names = [spec.name for spec in values.get("specs", [])]
        product_names = [product.name for product in values.get("products", [])]

        for item in api_catalog:
            if item.edgeAPIProductName not in product_names:
                raise ValueError(
                    f"edgeAPIProductName {item.edgeAPIProductName} not in list of products in this environment"
                )
            if item.specId and item.specId not in spec_names:
                raise ValueError(
                    f"specId {item.specId} not in list of specs in this environment"
                )
        return api_catalog

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
