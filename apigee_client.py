import requests
from functools import partialmethod


def raise_for_status_hook(response: requests.Response, *args, **kwargs):
    response.raise_for_status()


class ApigeeClient:
    def __init__(
        self,
        apigee_org: str,
        username: str = None,
        password: str = None,
        access_token: str = None,
        session: requests.Session = requests.Session(),
    ):
        self.apigee_org = apigee_org

        if access_token:
            self.access_token = access_token
        elif username and password:
            self.access_token = self._get_access_token(username, password)

        self._session = session
        self._session.hooks = {"response": raise_for_status_hook}

    def _request(self, method: str, url: str, **kwargs):
        headers = self._auth_headers

        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            del kwargs["headers"]

        return self._session.request(method, url, headers=headers, **kwargs)

    get = partialmethod(_request, "GET")
    post = partialmethod(_request, "POST")
    put = partialmethod(_request, "PUT")
    delete = partialmethod(_request, "DELETE")
    patch = partialmethod(_request, "PATCH")
    head = partialmethod(_request, "HEAD")
    options = partialmethod(_request, "OPTIONS")

    def list_proxies(self):
        response = self.get(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/apis"
        )
        return response.json()

    def list_env_proxy_deployments(self, env: str):
        response = self.get(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/environments/{env}/deployments"
        )
        return response.json()

    def get_proxy(self, proxy):
        response = self.get(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/apis/{proxy}"
        )
        return response.json()

    def get_proxy_revision(self, proxy: str, revision: str):
        response = self.get(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/apis/{proxy}/revisions/{revision}"
        )
        return response.json()

    def undeploy_proxy_revision(self, env: str, proxy: str, revision: str):
        response = self.delete(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/environments/{env}/apis/{proxy}/revisions/{revision}/deployments"
        )
        return response.json()

    def delete_proxy(self, proxy: str):
        response = self.delete(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/apis/{proxy}"
        )
        return response.json()

    def list_products(self):
        response = self.get(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/apiproducts"
        )
        return response.json()

    def delete_product(self, product: str):
        # TODO implement cascade behaviour
        response = self.delete(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/apiproducts/{product}"
        )
        return response.json()

    def list_specs(self):
        response = self.get(
            f"https://apigee.com/dapi/api/organizations/{self.apigee_org}/specs/folder/home"
        )
        return response.json()

    def create_spec(self, name: str, folder: str):
        response = self.post(
            f"https://apigee.com/dapi/api/organizations/{self.apigee_org}/specs/doc",
            json={"folder": folder, "name": name, "kind": "Doc"},
        )
        return response

    def update_spec(self, spec_id: str, content: str):
        response = self.put(
            f"https://apigee.com/dapi/api/organizations/{self.apigee_org}/specs/doc/{spec_id}/content",
            headers=dict(**{"Content-Type": "text/plain"}, **self._auth_headers),
            data=content.encode("utf-8"),
        )
        return response

    def delete_spec(self, spec_id: str):
        response = self.delete(
            f"https://apigee.com/dapi/api/organizations/{self.apigee_org}/specs/doc/{spec_id}",
        )
        return response

    def list_keystores(self, environment: str):
        response = self.get(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/environments/{environment}/keystores",
        )
        return response.json()

    def get_keystore(self, environment: str, keystore_name: str):
        response = self.get(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/environments/{environment}/keystores/{keystore_name}",
        )
        return response.json()

    def create_keystore(self, environment: str, keystore_name: str):
        """
        Create a return a keystore.

        Is idempotent, if keystore already exists will just retrieve.
        """
        if keystore_name in self.list_keystores(environment):
            return self.get_keystore(environment, keystore_name)

        response = self.post(
            f"https://api.enterprise.apigee.com/v1/organizations/{self.apigee_org}/environments/{environment}/keystores",
            data={"name": keystore_name},
        )

        return response.json()

    @property
    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get_access_token(self, username: str, password: str):
        response = self.post(
            "https://login.apigee.com/oauth/token",
            data={"username": username, "password": password, "grant_type": "password"},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "Basic ZWRnZWNsaTplZGdlY2xpc2VjcmV0",
            },
        )
        return response.json()["access_token"]
