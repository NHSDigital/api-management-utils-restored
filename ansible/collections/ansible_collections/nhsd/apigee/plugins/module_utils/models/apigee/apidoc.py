from typing import Optional
import pydantic


class ApigeeApidoc(pydantic.BaseModel):
    edgeAPIProductName: str
    anonAllowed: bool = True
    description: str = None
    requireCallbackUrl: bool = False
    title: str = None
    visibility: bool = False
    specId: str = ""
    specContent: str = ""

    class Config:
        extra = "forbid"
