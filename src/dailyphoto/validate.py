import os
from typing import Any

from .config import Config
from .config import get_metadata_filename
from .config import IMAGES
from .config import Metadata
from .config import METADATA_DIR
from .config import read_metadata


def valid_str(value: Any) -> bool:
    return isinstance(value, str) and len(value) > 0


def validate_metadata(meta_filename: str, meta: Metadata) -> bool:
    # TODO remove after validating that we don't need this
    ret = True
    if meta.model_extra and len(meta.model_extra.items()) > 0:
        print(f"{meta_filename} has extra fields: {meta.model_extra}")
        ret = False

    if not valid_str(meta.alt):
        print(f"{meta_filename} has invalid alt text: {meta.alt}")
        ret = False

    if not valid_str(meta.camera):
        print(f"{meta_filename} has invalid camera text: {meta.camera}")
        ret = False

    if not valid_str(meta.film):
        print(f"{meta_filename} has invalid film text: {meta.film}")
        ret = False

    if not valid_str(meta.subtitle):
        print(f"{meta_filename} has invalid subtitle text: {meta.subtitle}")
        ret = False

    if isinstance(meta.date, str):
        print(f"{meta_filename} has invalid date: {meta.date}")
        ret = False

    return ret


def validate(*, conf: Config) -> int:
    dates = conf.dates

    if dates is None or len(dates) == 0:
        print("No dates set in config")
        return 1

    ret = 0
    config_files = set()
    for date in dates:
        # Check for dupes in the filenames
        if date.filename in config_files:
            print(f"Entry {date}: {date.filename} is duplicate")
            ret += 1
        config_files.add(date.filename)

        if not os.path.exists(os.path.join(IMAGES, date.filename)):
            print(f"Entry {date}: {date.filename} missing jpg")
            ret += 1

        metadata_file = get_metadata_filename(METADATA_DIR, date.filename)
        metadata = read_metadata(metadata_file)

        if metadata is None:
            ret += 1
            print(f"Entry {date} unable to load {metadata_file}")
            continue

    disk_files = set()
    for root, dirs, files in os.walk(IMAGES):
        if root != IMAGES:
            print(f"{IMAGES} contains unknown dir {root}")
            ret += 1

        if len(dirs) != 0:
            print(f"extra dirs detected see {dirs}")
            ret += 1

        for file in files:
            disk_files.add(file)

    diff = config_files.difference(disk_files)
    if len(diff) != 0:
        print(
            f"Missing images in config_files {diff}",
        )

    diff = disk_files.difference(config_files)
    if len(diff) != 0:
        print(
            f"Unexpected files on disk: {diff}",
        )

    return ret
