import pydantic

from ansible_collections.nhsd.apigee.plugins.module_utils.models.manifest.manifest import Manifest


class ApplyPullRequestNamespace(pydantic.BaseModel):
    """
    This Model applies our pull-request namespacing for pipeline
    deployment.

    Once the object has been initialized it contains all the data
    needed for a pull-request deployment of what is in the manifest
    file.

    The validator:

        1. Removes all environments other than 'internal-dev' and
           'interal-dev-sandbox'

        2. Replaces all instances of 'internal-dev' with
           :param:`pull_request` in the name-like fields of the
           :class:`ApigeeApidoc`, :class:`ApigeeProduct`, and
           :class:`ApigeeSpec` objects.

    :param pull_request: A string like 'pr-1234' for pull request
        number 1234. Alternatively 'utils-pr-1234' for utils pull request number 1234
    :param manifest: The content of your manifest.yml.
    """

    pull_request: pydantic.constr(regex=r"^pr-[0-9]+$|^utils-pr-[0-9]+$")  # i.e. 'pr-1234' or 'utils-pr-1234'
    manifest: Manifest

    @pydantic.validator("manifest")
    def apply_namespace(cls, manifest, values):
        api_name = manifest.meta.api.name

        manifest.apigee.environments = [
            env for env in manifest.apigee.environments if env.name.startswith("internal-dev")
        ]

        # here we want:
        # canary-api-internal-dev         -> canary-api-pr-1234
        # canary-api-internal-dev-sandbox -> canary-api-pr-1234-sandbox
        # Canary API (Internal Development) -> [PR 1234] Canary API (Internal Development)
        old = "internal-dev"
        new = values["pull_request"]
        display = new.replace('-', ' ').upper()
        for env in manifest.apigee.environments:
            for product in env.products:
                product.name = product.name.replace(old, new, 1)
                product.displayName = f"[{display}] {product.displayName}"
                product.proxies = [
                    proxy.replace(old, new, 1)
                    if proxy.startswith(api_name)
                    else proxy
                    for proxy in product.proxies
                ]

            for spec in env.specs:
                spec.name = spec.name.replace(old, new, 1)
            
            # for entry in env.api_catalog:
            #     entry.edgeAPIProductName = entry.edgeAPIProductName.replace(
            #         old, new, 1
            #     )
            #     entry.title =  f"[{display}] {entry.title}"
            #     entry.specId = entry.specId.replace(old, new, 1)

        return manifest
