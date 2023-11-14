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


def select_unique(
    items: typing.List[typing.Dict[str, typing.Any]],
    key: str,
    value: str,
    valid_lengths: typing.Optional[typing.List[int]] = None,
) -> typing.List[typing.Dict[str, typing.Any]]:

    selected = [item for item in items if item.get(key) == value]
    if not valid_lengths:
        valid_lengths = [0, 1]
    if len(selected) not in valid_lengths:
        raise ValueError(f"{JSON.dumps(selected)}")
    return selected


def get_all_apidocs(organization, access_token, task_vars=None, refresh=False):
    """
    Get all apidocs for organization. Requires valid apigee acess_token.

    If task_vars is passed in, will search in there for the apidocs.
    If task_vars is included, will update the task_vars with APIGEE_APIDOCS.
    """
    if task_vars is None:
        task_vars = {}
    apidocs = task_vars.get("APIGEE_APIDOCS")
    if refresh or not apidocs:
        all_results = []

        params = {
            "pageSize" : 100
        }
        scan = True

        while scan:
            apidocs_request = get(constants.portal_uri(organization), access_token, params=params)
            if apidocs_request.get("failed"):
                return apidocs_request

            next_page_token = apidocs_request["response"]["body"]["next_page_token"]
            all_results += apidocs_request["response"]["body"]["data"]

            if next_page_token != "":
                params["pageToken"] = next_page_token
            else:
                scan = False

        task_vars.update({"APIGEE_APIDOCS": all_results})
    return task_vars


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
