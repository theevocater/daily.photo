import functools
import json
import os

from .types import Config

UNUSED = "queued"
UNUSED_IMAGES = os.path.join(UNUSED, "images")
UNUSED_METADATA = os.path.join(UNUSED, "metadata")
IMAGES = "current/images"
METADATA_DIR = "current/metadata"
OUTPUT_DIR = "generated"
OUTPUT_IMAGES = "images"
TEMPLATE = "template.html"


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
