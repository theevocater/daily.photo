import os
import shutil

from .config import Config
from .config import UNUSED
from .config import UNUSED_IMAGES
from .config import UNUSED_METADATA


def unused(conf: Config, new_image: str) -> bool:
    for date in conf.dates:
        if date.filename == new_image:
            print(f"{date.filename} is already used on {date.day}")
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


def queue_images(*, conf: Config, source_dir: str) -> int:
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
            if entry.is_file() and unused(conf, entry.name):
                ret = move(source_dir, entry.name)
                if ret != 0:
                    return ret

    return 0
