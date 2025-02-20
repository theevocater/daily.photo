import functools
import json
import os
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


@functools.cache
def read_config(config_file: str) -> dict[str, Any] | None:
    try:
        with open(config_file) as c:
            return json.load(c)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        print(f"Unable to load config_file: {config_file}.", e)
        return None


def get_metadata_filename(metadata_dir: str, image: str) -> str:
    return os.path.join(
        metadata_dir,
        os.path.splitext(os.path.basename(image))[0] + ".json",
    )
