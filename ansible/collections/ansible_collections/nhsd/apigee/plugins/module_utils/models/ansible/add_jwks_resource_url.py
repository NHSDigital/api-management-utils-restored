import pydantic
import typing
import requests
import os

from ansible_collections.nhsd.apigee.plugins.module_utils import utils
from ansible_collections.nhsd.apigee.plugins.module_utils.constants import (
    APIGEE_BASE_URL,
)

_cached_app_data = None
_environment = None
_app_id = None


def _put_app_data():
    return _cached_app_data


def default_jwks_resource_url(environment=None, app_id=None):
    if environment is None:
        global _environment
        environment = _environment
    if app_id is None:
        global _app_id
        app_id = _app_id
    return f"https://nhsdigital.github.io/identity-service-jwks/jwks/{environment}/{app_id}.json"


class AddJwksResourceUrlToApp(pydantic.BaseModel):
    organization: typing.Literal["nhsd-nonprod", "nhsd-prod"]
    environment: typing.Literal[
        "internal-dev",
        "internal-dev-sandbox",
        "internal-qa",
        "internal-qa-sandbox",
        "ref",
        "res",
        "dev",
        "int",
        "sandbox",
        "prod",
    ]
    access_token: str
    app_id: pydantic.UUID4
    jwks_resource_url: pydantic.HttpUrl = pydantic.Field(default_factory=default_jwks_resource_url)
    _app_data: typing.Dict = pydantic.PrivateAttr(default_factory=_put_app_data)

    @pydantic.validator("environment")
    def check_org_env_combo(cls, environment, values):
        org = values.get("organization")
        if org is None:
            return
        non_prod_envs = [
            "internal-dev",
            "internal-dev-sandbox",
            "internal-qa",
            "internal-qa-sandbox",
            "ref",
            "res",
        ]
        if org == "nhsd-nonprod" and environment not in non_prod_envs:
            raise ValueError(f"Invalid environment {environment} for organization {org}")
        return environment

    @pydantic.validator("environment")
    def cache_put(cls, environment):
        global _environment
        _environment = environment
        return environment

    @pydantic.validator("app_id")
    def check_app_exists(cls, app_id, values):
        access_token = values.get("access_token")
        org = values.get("organization")
        url = f"{APIGEE_BASE_URL}organizations/{org}/apps/{app_id}"
        app_response = utils.get(url, access_token)

        if app_response.get("failed"):
            raise ValueError(f"Unable to find app with app_id {app_id} in {org}")

        app_data = app_response["response"]["body"]
        attributes = app_data.get("attributes", [])
        jwks_attribs = [a for a in attributes if a["name"] == "jwks-resource-url"]
        if len(jwks_attribs) > 1:
            raise ValueError(
                f"App {app_id} has {len(jwks_attribs)} jwks-resource-url attributes! {[v['value'] for v in jwks_attribs]}"
            )

        # cache response data
        global _cached_app_data
        _cached_app_data = app_data
        global _app_id
        _app_id = app_id
        return app_id

    @pydantic.validator("jwks_resource_url", always=True)
    def check_jwks_url(cls, jwks_resource_url):
        skip_validation = os.environ.get("SKIP_JWKS_RESOURCE_URL_VALIDATION")
        if skip_validation:
            return jwks_resource_url

        resp = requests.get(jwks_resource_url)
        if resp.status_code != 200:
            raise ValueError(f"Invalid jwks_resource_url: GET {jwks_resource_url} returned {resp.status_code}")
        try:
            resp.json()
        except Exception:
            raise ValueError(
                f"Invalid jwks_resource_url: GET {jwks_resource_url} returned {resp.content.decode()}, which is not valid JSON"
            )
        return jwks_resource_url
