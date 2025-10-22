APIGEE_BASE_URL = "https://api.enterprise.apigee.com/v1/"
APIGEE_DAPI_URL = "https://apigee.com/dapi/api/"

APIGEE_ORG_TO_ENV = {
    "nhsd-nonprod": [
        "internal-dev",
        "internal-dev-sandbox",
        "internal-qa",
        "internal-qa-sandbox",
        "ref",
        "res",
    ],
    "nhsd-prod": ["dev", "int", "sandbox", "prod"],
}
