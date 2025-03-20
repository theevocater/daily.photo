import os
import random
import shutil
from datetime import datetime
from datetime import timedelta

from . import config


def new(
    *,
    images: list[str] | None,
    dates: list[str] | None,
    config_file: str,
) -> int:
    # Possible conditions:
    # dates is none, images is none
    # add as many images as possible from last to now
    # dates is not none, images is none
    # add images for every date specified, bail if there aren't enough
    # dates is not none, images is not none
    # add those images for dates specified, bail if they aren't equal
    # dates is None, images is not none
    # choose from these images, from last date til today

    # load the last day set in the conf file
    conf = config.read_config(config_file)
    if conf is None:
        return 1
    all_dates = conf.dates
    if all_dates is None:
        # if there are no dates in the config, bail, something is wrong
        return 1
    sorted(all_dates, key=lambda x: x.day)
    last_day = datetime.strptime(all_dates[-1].day, "%Y%m%d")

    # get a list of all potential unused images
    unused_images = [photo for photo in os.listdir(config.UNUSED_IMAGES)]

    # This logic seems complicated BUT
    max_days = min(
        [  # Take the longer of dates and images
            max(
                [
                    len(dates) if dates is not None else 0,
                    len(images) if images is not None else 0,
                ],
            )  # or if thats not set, the number of days since the last
            or (datetime.now() - last_day).days,
            # but we only have unused_images, so no longer than that
            len(unused_images),
        ],
    )

    if images is None:
        images = []
    for image in images:
        if image in unused_images:
            unused_images.remove(image)
    if max_days - len(images) > 0:
        images += random.sample(unused_images, max_days - len(images))

    if dates is None:
        dates = []
    else:
        last_day = datetime.strptime(dates[-1], "%Y%m%d")

    dates += [
        (last_day + timedelta(days=(i + 1))).strftime("%Y%m%d")
        for i in range(0, max_days - len(dates))
    ]

    for date, image in zip(dates, images):
        new_image(
            new_date=date,
            new_image=image,
            config_file=config_file,
        )
    return 0


def new_image(
    *,
    new_date: str,
    new_image: str,
    config_file: str,
) -> int:
    """
    Choose and move a new image to IMAGES
    """
    conf = config.read_config(config_file)
    if conf is None:
        return 1

    # Detect if a date or image has been used before
    for date in conf.dates:
        if date.day == new_date:
            print(f"Error: already have an image for {new_date}")
            return 1
        if new_image and date.filename == new_image:
            print(f"Error: {new_image} was already used on {date.day}")
            return 1

    # Move the image
    new_image = os.path.basename(new_image)

    old_image_path = os.path.join(config.UNUSED_IMAGES, new_image)
    if not os.path.exists(old_image_path):
        print(f"Error: {old_image_path} does not exist")
        return 1
    new_image_path = os.path.join(config.IMAGES, new_image)
    print(f"Moving {old_image_path} to {new_image_path}")
    shutil.move(old_image_path, new_image_path)

    # Try to move the metadata file
    old_metadata_file = config.get_metadata_filename(
        config.UNUSED_METADATA,
        new_image,
    )
    if os.path.exists(old_metadata_file):
        new_metadata_file = config.get_metadata_filename(
            config.METADATA_DIR,
            new_image,
        )
        print(f"Moving {old_metadata_file} to {new_metadata_file}")
        shutil.move(old_metadata_file, new_metadata_file)
    else:
        print(f"{old_metadata_file} does not exist, no need to move")

    conf.dates.append(config.Date(day=new_date, filename=new_image))
    print(f"Writing {config_file}")
    config.write_config(config_file, conf)

    print(f"Added {new_date}: {new_image}")
    return 0
