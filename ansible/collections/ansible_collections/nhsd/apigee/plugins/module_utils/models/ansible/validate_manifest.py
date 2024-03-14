import os
import re
import pydantic
from ansible_collections.nhsd.apigee.plugins.module_utils.models.manifest.manifest import (
    Manifest,
)


def correct_namespace(name, api_name, env_name) -> bool:
    """
    Checks that a name of a thing we want to create in Apigee matches our namespacing conventions.

    e.g. for api_name="canary-api" and env_name="internal-dev"
    |--------------------------------------------------------------+--------|
    | name                                                         | result |
    |--------------------------------------------------------------+--------|
    | "canary-api-internal-dev"                                    | True   |
    | "canary-api-extra-thing-internal-dev"                        | True   |
    | "canary-apiinternal-dev"                                     | False  |
    | "canary-api-internal-dev-application-restricted"             | True   |
    | "canary-api-extra-thing-internal-dev-application-restricted" | True   |
    |--------------------------------------------------------------+--------|

    :param name: Name of thing in Apigee.
    :param api_name: The meta.api.name item from your manifest
    :param env_name: The environment name (e.g. 'internal-dev', 'int', or 'prod')
    """
    regex = f"^{api_name}(-[a-z0-9]+)*-{env_name}(-[a-z0-9]+)*$"
    return bool(re.match(regex, name))


class ValidateManifest(pydantic.BaseModel):
    dist_dir: pydantic.DirectoryPath = ""
    manifest: Manifest
    service_name: str = ""

    @pydantic.validator("service_name")
    def check_service_name(cls, service_name, values):
        if service_name:
            manifest = values.get("manifest")
            if not manifest:
                return
            meta = manifest.meta
            if not meta:
                return
            api_name = meta.api.name
            if not re.match(f"{api_name}(-[a-z]+)*", service_name):
                raise ValueError(
                    f"pipeline defined SERVICE_NAME ('{service_name}') does not begin with manifest defined meta.api.name ('{api_name}')"
                )

    @pydantic.validator("manifest", pre=True)
    def prepend_dist_dir_to_spec_paths(cls, manifest, values):
        dist_dir = values.get("dist_dir")
        print(dist_dir)
        if not dist_dir:
            return manifest
        apigee = manifest["apigee"]
        for env_dict in apigee["environments"]:
            for spec_dict in env_dict["specs"]:
                path = spec_dict.get("path")
                if path is not None:
                    spec_dict["path"] = os.path.join(dist_dir, path)
        return manifest

    @pydantic.validator("manifest")
    def check_namespacing(cls, manifest, values):
        if not manifest.meta:
            return
        api_name = manifest.meta.api.name

        for env in manifest.apigee.environments:
            if env is None:
                continue
            for product in env.products:
                if not correct_namespace(product.name, api_name, env.name):
                    raise ValueError(
                        f"{product.name} does not conform to namespace {api_name}-*{env.name}"
                    )
            for spec in env.specs:
                if not correct_namespace(spec.name, api_name, env.name):
                    raise ValueError(
                        f"{spec.name} does not conform to namespace for {api_name}-*{env.name}"
                    )
        return manifest
