import pydantic
import typing
import yaml


class ApigeeSpec(pydantic.BaseModel):
    name: str
    path: pydantic.FilePath
    content: typing.Optional[typing.Dict] = None

    @pydantic.validator("content", always=True)
    def load_content(cls, content, values):
        if content is not None:
            return content
        path = values.get("path")
        if not path:  # When path does not validate.
            return None
        with open(path) as f:
            try:
                yaml_content = yaml.safe_load(f.read())
            except Exception as e:
                raise ValueError(str(e))
        return yaml_content

    def dict(self, **kwargs):
        # The pydantic.FilePath object validates that the file exists,
        # which is nice. However, ansible does not understand this
        # object so we convert it back to a string for export.
        native = super().dict(**kwargs)
        native.update({"path": str(native["path"])})
        if native.get("guid"):
            native.update({"guid": str(native["guid"])})
        return native

    class Config:
        extra = "forbid"
