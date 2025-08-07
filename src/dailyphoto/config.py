import functools
import json
import os
from datetime import datetime
from typing import Annotated

from annotated_types import Len
from pydantic import BaseModel
from pydantic import BeforeValidator
from pydantic import ConfigDict
from pydantic import PlainSerializer
from pydantic import ValidationError

UNUSED = "queued"
UNUSED_IMAGES = os.path.join(UNUSED, "images")
UNUSED_METADATA = os.path.join(UNUSED, "metadata")
IMAGES = "current/images"
METADATA_DIR = "current/metadata"
OUTPUT_DIR = "generated"
OUTPUT_IMAGES = "images"
TEMPLATE = "template.html"


ShortDatetime = Annotated[
    datetime,
    BeforeValidator(lambda ds: datetime.strptime(ds, "%Y%m%d")),
    PlainSerializer(lambda dt: dt.strftime("%Y%m%d") if dt else ""),
]


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


def get_metadata_filename(metadata_dir: str, image: str) -> str:
    return os.path.join(
        metadata_dir,
        os.path.splitext(os.path.basename(image))[0] + ".json",
    )


def read_metadata(metadata_file: str) -> Metadata | None:
    try:
        with open(metadata_file) as c:
            parsed = json.load(c)
            return Metadata.model_validate(parsed)
    except (FileNotFoundError, json.decoder.JSONDecodeError, ValidationError) as e:
        print(f"Unable to load metadata: {metadata_file}.", str(e))
        return None


def write_metadata(metadata_file: str, metadata: Metadata | MetadataEditable) -> None:
    try:
        with open(metadata_file, "w") as c:
            c.write(metadata.model_dump_json(indent=2))
            # include a final line ending
            c.write("\n")
    except OSError as e:
        print(f"Unable to write metadata: {metadata_file}.", e)


class Date(BaseModel):
    day: ShortDatetime
    filename: str


class Config(BaseModel):
    dates: list[Date]


@functools.cache
def read_config(config_file: str) -> Config | None:
    try:
        with open(config_file) as c:
            parsed = json.load(c)
            return Config.model_validate(parsed)

    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        print(f"Unable to load config_file: {config_file}.", e)
        return None


def write_config(config_file: str, config: Config) -> None:
    try:
        with open(config_file, "w") as c:
            c.write(config.model_dump_json(indent=2))
            # include a final line ending
            c.write("\n")

    except OSError as e:
        print(f"Unable to write config_file: {config_file}.", e)
