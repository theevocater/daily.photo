import functools
import json
import os
from dataclasses import dataclass
from typing import Any

UNUSED = "queued"
UNUSED_IMAGES = os.path.join(UNUSED, "images")
UNUSED_METADATA = os.path.join(UNUSED, "metadata")
IMAGES = "current/images"
METADATA_DIR = "current/metadata"
OUTPUT_DIR = "generated"
OUTPUT_IMAGES = "images"
TEMPLATE = "template.html"

METADATA_TEMPLATE = {
    "alt": "",
    "camera": "",
    "date": "",
    "film": "",
    "subtitle": "",
}


@dataclass
class Date:
    day: str
    filename: str

    def to_json(self):
        return json.dumps([self.day, self.filename])


@dataclass
class Config:
    dates: list[Date]

    @classmethod
    def from_json(cls, js: Any) -> "Config":
        return Config(
            dates=[Date(day=date[0], filename=date[1]) for date in js["dates"]],
        )

    def to_json(self):
        return json.dumps(
            {"dates": [[d.day, d.filename] for d in self.dates]},
            indent=2,
        )


@functools.cache
def read_config(config_file: str) -> Config | None:
    try:
        with open(config_file) as c:
            parsed = json.load(c)
            return Config.from_json(parsed)

    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        print(f"Unable to load config_file: {config_file}.", e)
        return None


def write_config(config_file: str, config: Config) -> None:
    try:
        with open(config_file, "w") as c:
            c.write(config.to_json())

    except OSError as e:
        print(f"Unable to write config_file: {config_file}.", e)


def get_metadata_filename(metadata_dir: str, image: str) -> str:
    return os.path.join(
        metadata_dir,
        os.path.splitext(os.path.basename(image))[0] + ".json",
    )
