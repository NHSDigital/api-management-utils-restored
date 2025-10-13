import os


def _localstack() -> bool:
    """
    Returns True if environment variable APIM_INFRA_LOCALSTACK is set
    to something truthy.
    """
    return bool(os.environ.get("APIM_INFRA_LOCALSTACK"))


def api_registry() -> str:
    if _localstack():
        return "http://localhost:9000"
    return "https://api-registry.ptlrestored.api.platform.nhs.uk:9000"
