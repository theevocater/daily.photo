import functools
import json
import logging
import os

from .types import Config

logger = logging.getLogger(__name__)

UNUSED = "queued"
UNUSED_IMAGES = os.path.join(UNUSED, "images")
UNUSED_METADATA = os.path.join(UNUSED, "metadata")
IMAGES = "current/images"
METADATA_DIR = "current/metadata"
OUTPUT_DIR = "generated"
OUTPUT_IMAGES = "images"


@functools.cache
def read_config(config_file: str) -> Config | None:
    try:
        with open(config_file) as c:
            parsed = json.load(c)
            config = Config.model_validate(parsed)
            config.dates.sort(key=lambda d: d.day)
            return config

    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.error(f"Unable to load config_file: {config_file}. {e}")
        return None


def write_config(config_file: str, config: Config) -> None:
    try:
        config.dates.sort(key=lambda d: d.day)
        with open(config_file, "w") as c:
            c.write(config.model_dump_json(indent=2))
            # include a final line ending
            c.write("\n")

    except OSError as e:
        logger.error(f"Unable to write config_file: {config_file}. {e}")
