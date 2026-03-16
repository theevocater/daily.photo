import logging
import os
import random
import shutil
from datetime import datetime
from datetime import timedelta

from dailyphoto import kitty
from dailyphoto.metadata import update
from dailyphoto.types import Date

from .config import IMAGES
from .config import METADATA_DIR
from .config import Config
from .config import write_config

logger = logging.getLogger(__name__)


def unused(conf: Config, new_image: str) -> bool:
    for date in conf.dates:
        if date.filename == new_image:
            logger.error(f"{date.filename} is already used on {date.day}")
            return False
    return True


def queue_image(
    *,
    new_date: datetime,
    new_image: os.DirEntry,
    conf: Config,
    config_file: str,
) -> int:
    date_to_add = Date.model_validate({"day": new_date, "filename": new_image.name})

    final_path = os.path.join(IMAGES, date_to_add.filename)

    logger.info(f"Moving {new_image.path} to {final_path}")
    shutil.move(new_image.path, final_path)

    conf.dates.append(date_to_add)

    logger.info(f"Writing {config_file}")
    write_config(config_file, conf)
    return 0


def queue_images(*, conf: Config, config_file: str, source_dir: str) -> int:
    if not os.path.exists(source_dir):
        logger.error(f"Error: unable to list {source_dir}")
        return 1

    id = kitty.new_window()
    kitty.set_layout("horizontal")
    with os.scandir(source_dir) as e:
        entries = list(e)
        random.shuffle(entries)
        date = conf.dates[-1].day
        for entry in entries:
            _, ext = os.path.splitext(entry.name)
            if entry.is_file() and ext.lower() in (".png", ".jpg") and unused(conf, entry.name):
                date = date + timedelta(days=(1))
                ret = queue_image(
                    new_date=date,
                    new_image=entry,
                    conf=conf,
                    config_file=config_file,
                )
                if ret != 0:
                    return ret

                prefix, _ = os.path.splitext(entry.name)
                ret += update(
                    os.path.join(IMAGES, entry.name),
                    os.path.join(METADATA_DIR, prefix + os.path.extsep + "json"),
                    True,
                    id,
                )
    kitty.close_window(id)
    logger.info(f"Writing {config_file}")
    write_config(config_file, conf)

    return 0
