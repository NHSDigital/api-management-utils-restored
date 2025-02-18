import os
import json
import time
from json import JSONDecodeError
from typing import Dict, Any

import requests


class AzureDevOps:

    def __init__(self):
        self.base_url = "https://dev.azure.com/NHSD-APIM/API Platform/_apis/pipelines"
        self.client_id = os.environ["AZ_CLIENT_ID"]
        self.client_secret = os.environ["AZ_CLIENT_SECRET"]
        self.client_tenant = os.environ["AZ_CLIENT_TENANT"]
        self.access_token = self._get_access_token()
        self.token = self.access_token
        self.auth = requests.auth.HTTPBasicAuth("", self.token)
        self.notify_commit_sha = os.environ["NOTIFY_COMMIT_SHA"]
        self.utils_pr_number = os.environ["UTILS_PR_NUMBER"]
        self.notify_github_repo = "NHSDigital/api-management-utils"
        self.api_request_delay = 60

    @staticmethod
    def print_response(response: requests.Response, note: str, verbose: bool = True) -> None:
        if verbose:
            print(note)
            try:
                print(json.dumps(response.json(), indent=2))
            except json.decoder.JSONDecodeError:
                print(response.content.decode())

    def run_pipeline(self,
                     service: str,
                     pipeline_type: str,
                     pipeline_id: int,
                     pipeline_branch: str) -> int:

        run_url = self.base_url + f"/{pipeline_id}/runs"
        request_body = self._build_request_body(pipeline_branch)

        response = self.api_request(
            run_url,
            json=request_body,
            method='post',
        )
        self.print_response(response, f"Initial request to {run_url}")

        result = "failed"
        if response.status_code == 200:
            result = self._check_pipeline_response(response)
            print(f"Result of {service} {pipeline_type} pipeline: {result}")
        else:
            print(f"Triggering pipeline: {service} {pipeline_type} failed, status code: {response.status_code}")
        return result

    def _check_pipeline_response(self, response: requests.Response):
        delay = 0
        state_url = response.json()["_links"]["self"]["href"]
        while response.status_code == 200 and response.json()["state"] == "inProgress":
            time.sleep(self.api_request_delay)
            delay = delay + self.api_request_delay
            state_response = self.api_request(state_url)
            self.print_response(state_response, f"Response from {state_url} after {delay} seconds")
        return response.json()["result"]

    def _build_request_body(self, pipeline_branch: str):
        return {
            "resources": {
                "repositories": {
                    "common": {
                        "repository": {
                            "fullName": "NHSDigital/api-management-utils",
                            "type": "gitHub",
                        },
                        "refName": f"refs/pull/{self.utils_pr_number}/merge",
                    },
                    "self": {"refName": f"{pipeline_branch}"},
                }
            },
            "variables": {
                "NOTIFY_GITHUB_REPOSITORY": {
                    "isSecret  ": False,
                    "value": f"{self.notify_github_repo}",
                },
                "NOTIFY_COMMIT_SHA": {
                    "isSecret  ": False,
                    "value": f"{self.notify_commit_sha}"
                },
                "UTILS_PR_NUMBER": {
                    "isSecret  ": False,
                    "value": f"{self.utils_pr_number}",
                }
            }
        }

    def _get_access_token(self):
        url = f"https://login.microsoftonline.com/{self.client_tenant}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://app.vssps.visualstudio.com/.default",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        res = requests.post(url=url, data=data, headers=headers)
        res.raise_for_status()

        return res.json()["access_token"]

    def api_request(
        self,
        uri,
        params: Dict[str, Any] = None,
        headers: Dict[str, Any] = None,
        api_version: str = "6.0-preview.1",
        method: str = "get",
        max_tries: int = 5,
        **kwargs,
    ):
        def get_headers():

            _headers = {"Accept": "application/json", "Authorization": f"Bearer {self.access_token}"}
            _headers.update(headers or {})
            return _headers

        _params = {"api-version": api_version}
        _params.update(params or {})
        action = getattr(requests, method)

        result = action(uri, params=_params, headers=get_headers(), **kwargs)
        tries = 0
        while result.status_code not in (200, 201, 202, 204):
            tries += 1

            if tries > max_tries:
                break

            if result.status_code in (203, 401):
                print("REFRESHING ACCESS TOKEN...")
                self.access_token = self._get_access_token()

            time.sleep(0.5 * tries)
            result = action(uri, params=_params, headers=get_headers(), **kwargs)

        return result
