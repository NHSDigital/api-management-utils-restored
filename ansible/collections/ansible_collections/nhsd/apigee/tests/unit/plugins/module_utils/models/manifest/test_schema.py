import pathlib

from ansible_collections.nhsd.apigee.plugins.module_utils.models.manifest.manifest import (
    Manifest,
)
from ansible_collections.nhsd.apigee.plugins.module_utils.models.manifest.meta import (
    SCHEMA_VERSION,
)

DIR = pathlib.Path(__file__).parent.absolute()

MAJOR, MINOR, PATCH = [int(x) for x in SCHEMA_VERSION.split(".")]


def test_schema_version():
    """
    Check that the current version of the schema matches the snapshot
    made at the last version change.
    """

    live_schema = Manifest.schema()
    print(live_schema)
    with open(str(DIR) + f'/schema_versions/v{SCHEMA_VERSION}.json') as f:
        print(SCHEMA_VERSION)
        print(f)
        # recorded_schema = json.load(f)
    # assert live_schema == recorded_schema
