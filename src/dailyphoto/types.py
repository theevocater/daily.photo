from datetime import datetime
from typing import Annotated

from annotated_types import Len
from pydantic import BaseModel
from pydantic import BeforeValidator
from pydantic import ConfigDict
from pydantic import PlainSerializer


ShortDatetime = Annotated[
    datetime,
    BeforeValidator(lambda ds: datetime.strptime(ds, "%Y%m%d")),
    PlainSerializer(lambda dt: dt.strftime("%Y%m%d") if dt else ""),
]


class Date(BaseModel):
    day: ShortDatetime
    filename: str


class Config(BaseModel):
    dates: list[Date]


class MetadataEditable(BaseModel):
    """Represents newly generated image metadata. Used for adding + editing images when fields might be unset"""

    model_config = ConfigDict(extra="allow")
    alt: str = ""
    camera: str = ""
    date: ShortDatetime | str | None = None
    film: str = ""
    subtitle: str = ""


class Metadata(BaseModel):
    """
    Represents the final image metadata.
    Used for validation and generation to ensure that all fields are filled in and have certain properties.
    """

    model_config = ConfigDict(extra="forbid")
    alt: Annotated[str, Len(min_length=1)]
    camera: Annotated[str, Len(min_length=1)]
    date: ShortDatetime
    film: Annotated[str, Len(min_length=1)]
    subtitle: Annotated[str, Len(min_length=1)]
