import os
import shutil
from typing import Any

from .config import UNUSED
from .config import UNUSED_IMAGES
from .config import UNUSED_METADATA


def unused(dates: list[tuple[str, str]], new_image: str) -> bool:
    for date, image in dates:
        if image == new_image:
            print(f"{image} is already used on {date}")
            return False
        if os.path.exists(os.path.join(UNUSED_IMAGES, new_image)):
            print(f"{new_image} is already in {UNUSED_IMAGES}")
            return False
    return True


def move(
    source_dir: str,
    name: str,
) -> int:
    _, ext = os.path.splitext(name)
    if ext != ".jpg":
        return 0
    print(
        f"Moving {source_dir}/{name} to {UNUSED_IMAGES}/{name}",
    )
    shutil.move(
        os.path.join(source_dir, name),
        os.path.join(UNUSED_IMAGES, name),
    )

    return 0


def queue_images(conf: dict[str, Any], source_dir: str) -> int:
    dates = conf.get("dates", None)
    if dates is None:
        print("Unable to get dates from config")
        return 1

    if not os.path.exists(source_dir):
        print(f"Error: unable to list {source_dir}")
        return 1

    if not os.path.exists(UNUSED):
        os.mkdir(UNUSED)
    if not os.path.exists(UNUSED_IMAGES):
        os.mkdir(UNUSED_IMAGES)
    if not os.path.exists(UNUSED_METADATA):
        os.mkdir(UNUSED_METADATA)

    with os.scandir(source_dir) as it:
        for entry in it:
            if entry.is_file() and unused(dates, entry.name):
                ret = move(source_dir, entry.name)
                if ret != 0:
                    return ret

    return 0
