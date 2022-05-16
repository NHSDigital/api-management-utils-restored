import pydantic
import typing


from ansible_collections.nhsd.apigee.plugins.module_utils.paas import api_registry

SCHEMA_VERSION = "1.1.5"

_REGISTRY_DATA = {}



class ManifestMetaApi(pydantic.BaseModel):
    name: pydantic.constr(regex=r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
    id: typing.Optional[pydantic.UUID4] = pydantic.Field(
        None, description="This field is deprecated, use guid instead."
    )
    guid: typing.Optional[pydantic.UUID4] = None
    spec_guids: typing.Optional[typing.Set[pydantic.UUID4]] = None

    def dict(self, **kwargs):
        native = super().dict(**kwargs)
        spec_guids = native.get("spec_guids")
        if spec_guids is None:
            spec_guids = []
        if "id" in native:  # Deprecated, do not export
            native.pop("id")
        native.update(
            {
                "guid": str(native["guid"]),
                "spec_guids": [str(guid) for guid in spec_guids],
             }
        )
        return native

    @pydantic.validator("guid", pre=True, always=True)
    def id_to_guid(cls, guid, values):
        """
        If using an old version of the manifest, this sets the 'guid'
        attribute from the now deprecated 'id' attribute.
        """
        _id = values.get("id")
        if _id and not guid:
            return _id
        return guid

    @pydantic.validator("name")
    def set_global_name(cls, name):
        _REGISTRY_DATA[name] = api_registry.get(name)
        return name

    @pydantic.validator("guid")
    def validate_guid(cls, guid, values):
        name = values.get("name")
        if name not in _REGISTRY_DATA:
            return  # Other problems.
        if guid is None:
            guid = _REGISTRY_DATA[name]["guid"]
        registered_guid = _REGISTRY_DATA[name]["guid"]
        if str(guid) != registered_guid:
            raise ValueError(f"Supplied guid {guid} does not match registered guid {registered_guid}")
        return guid

    @pydantic.validator("spec_guids")
    def validate_spec_guids(cls, spec_guids, values):
        # In theory these could be added over time, so for backwards
        # compatibility we just assert that the presented spec guids
        # are present
        name = values.get("name")
        if name not in _REGISTRY_DATA:
            return  # Other problems.
        if spec_guids is None:
            spec_guids = _REGISTRY_DATA[name]["spec_guids"]
        registered_spec_guids = _REGISTRY_DATA[name]["spec_guids"]

        invalid = []
        for spec_guid in spec_guids:
            if str(spec_guid) not in registered_spec_guids:
                invalid.append(str(spec_guid))
        if len(invalid) > 0:
            raise ValueError(f"Supplied spec_guids {invalid} do not match registered spec_guids {registered_spec_guids}")
        return spec_guids



class ManifestMeta(pydantic.BaseModel):
    schema_version: pydantic.constr(regex=r"[1-9][0-9]*(\.[0-9]+){0,2}")
    api: ManifestMetaApi

    @pydantic.validator("schema_version")
    def validate_schema_version(cls, schema_version):
        semantic_parts = schema_version.split(".")

        MAJOR, MINOR, PATCH = [int(x) for x in SCHEMA_VERSION.split(".")]
        major = int(semantic_parts[0])

        # Checking against minor/patch would not allow to us deploy
        # older versions of the manifest, which would be bad.
        if major != MAJOR:
            raise ValueError(
                f"Current schema version is {SCHEMA_VERSION}. "
                + "All minor and patch changes are backwards compatible."
            )

        return schema_version
