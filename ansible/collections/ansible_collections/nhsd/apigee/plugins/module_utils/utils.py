import json as JSON
import ansible
import deepdiff
import requests
import typing

from ansible_collections.nhsd.apigee.plugins.module_utils import constants


def exclude_keys(dict_, keys_to_ignore):
    return {k: v for k, v in dict_.items() if k not in keys_to_ignore}


def delta(before, after, keys_to_ignore=None):
    if not keys_to_ignore:
        keys_to_ignore = []
    return JSON.loads(
        deepdiff.DeepDiff(
            before,
            after,
            ignore_order=True,
            ignore_type_in_groups=[(ansible.utils.unsafe_proxy.AnsibleUnsafeText,str)],
            exclude_paths=[f"root['{key}']" for key in keys_to_ignore],
        ).to_json()
    )


def request(method, url, access_token, json=None, headers=None, status_code=None, session=None, params=None):
    if not status_code:
        status_code = [200]

    if not headers:
        headers = {}

    headers["authorization"] = f"Bearer {access_token}"

    if session is None:
        session = requests
    response = session.request(method, url, json=json, headers=headers, params=params)

    response_dict = {
        "response": {"status_code": response.status_code, "reason": response.reason,},
        "allowed_status_codes": status_code,
    }

    if response.status_code not in status_code:
        response_dict["failed"] = True

    content = response.content.decode()
    if len(content) == 0:
        response_dict["response"]["body"] = content
    else:
        try:
            response_dict["response"]["body"] = response.json()
        except JSON.decoder.JSONDecodeError:
            response_dict["failed"] = True
            response_dict["response"]["body"] = content

    if response_dict.get("failed"):
        response_dict["msg"] = f"Unexpected response from {method} {url}"

    return response_dict


def get(url, access_token, **kwargs):
    return request("GET", url, access_token, **kwargs)


def post(url, access_token, **kwargs):
    return request("POST", url, access_token, **kwargs)


def put(url, access_token, **kwargs):
    return request("PUT", url, access_token, **kwargs)


def get_all_spec_resources(organization, access_token, task_vars=None, refresh=False):
    """
    Get all spec_resources for organization.  Requires valid apigee
    acess_token.

    If task_vars is passed in, will search in there for the
    spec_resources.  If task_vars is included, will update the
    task_vars with APIGEE_SPEC_RESOURCES and APIGEE_SPEC_FOLDER_ID.
    """
    if task_vars is None:
        task_vars = {}
    spec_resources = task_vars.get("APIGEE_SPEC_RESOURCES")
    if refresh or not spec_resources:
        specs_list_uri = constants.APIGEE_DAPI_URL + f"/organizations/{organization}/specs/folder/home"
        all_specs_response = get(specs_list_uri, access_token)
        all_specs = all_specs_response["response"]["body"]
        if all_specs.get("failed"):
            return all_specs
        task_vars["APIGEE_SPEC_RESOURCES"] = all_specs["contents"]
        task_vars["APIGEE_SPEC_FOLDER_ID"] = all_specs["id"]

    return task_vars
