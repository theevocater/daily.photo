import json
import os
from datetime import datetime
from typing import Any

from .config import Config
from .config import get_metadata_filename
from .config import IMAGES
from .config import METADATA_DIR


def valid_str(value: Any) -> bool:
    return isinstance(value, str) and len(value) > 0


def valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    day = value
    if len(day) != 8:
        return False
    try:
        datetime.strptime(day, "%Y%m%d")
    except ValueError:
        return False
    return True


def validate(*, conf: Config) -> int:
    dates = conf.dates

    if dates is None or len(dates) == 0:
        print("No dates set in config")
        return 1

    metadata_keys = {
        "alt": valid_str,
        "camera": valid_str,
        "date": valid_date,
        "film": valid_str,
        "subtitle": valid_str,
    }

    ret = 0
    for date in dates:
        if not os.path.exists(os.path.join(IMAGES, date.filename)):
            print(f"Entry {date}: {date.filename} missing jpg")
            ret += 1

        metadata_file = get_metadata_filename(METADATA_DIR, date.filename)
        try:
            with open(metadata_file) as md:
                metadata = json.load(md)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            ret += 1
            print(f"Entry {date} unable to load {metadata_file}: ", e)
            continue

        for key, validator in metadata_keys.items():
            if key not in metadata:
                print(f'{metadata_file} missing key "{key}"')
                ret += 1
                continue

            if not validator(metadata[key]):
                print(
                    f"{metadata_file} unable to validate: {key} -> {metadata[key]}",
                )
                ret += 1
            del metadata[key]

        if len(metadata) > 0:
            print(f"{metadata_file} has extra keys {metadata.keys()}")
            ret += 1

    return ret
