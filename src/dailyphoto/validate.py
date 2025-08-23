import logging
import os

from .config import IMAGES
from .config import METADATA_DIR
from .config import Config
from .metadata import get_metadata_filename
from .metadata import read_metadata

logger = logging.getLogger(__name__)


def validate(*, conf: Config) -> int:
    dates = conf.dates

    if dates is None or len(dates) == 0:
        logger.error("No dates set in config")
        return 1

    ret = 0
    config_files = set()
    date_set = set()
    for date in dates:
        # Check for duplicate dates
        if date.day in date_set:
            logger.error(f"{date.day} exists more than once.")
            ret += 1
        date_set.add(date.day)

        # Check for dupes in the filenames
        if date.filename in config_files:
            logger.error(f"Entry {date}: {date.filename} is duplicate")
            ret += 1
        config_files.add(date.filename)

        if not os.path.exists(os.path.join(IMAGES, date.filename)):
            logger.error(f"Entry {date}: {date.filename} missing jpg")
            ret += 1

        metadata_file = get_metadata_filename(METADATA_DIR, date.filename)
        metadata = read_metadata(metadata_file)

        if metadata is None:
            ret += 1
            logger.error(f"Entry {date} unable to load {metadata_file}")
            continue

    disk_files = set()
    for root, dirs, files in os.walk(IMAGES):
        if root != IMAGES:
            logger.error(f"{IMAGES} contains unknown dir {root}")
            ret += 1

        if len(dirs) != 0:
            logger.error(f"extra dirs detected see {dirs}")
            ret += 1

        for file in files:
            disk_files.add(file)

    diff = config_files.difference(disk_files)
    if len(diff) != 0:
        logger.error(f"Missing images in config_files {diff}")

    diff = disk_files.difference(config_files)
    if len(diff) != 0:
        logger.error(f"Unexpected files on disk: {diff}")

    return ret
