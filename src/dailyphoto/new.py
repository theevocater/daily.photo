import datetime
import json
import os
import random
import shutil

from . import config


def new(
    *,
    images: list[str] | None,
    dates: list[str] | None,
    config_file: str,
) -> int:
    if dates is None:
        dates = []

    # ensure the images array is the same length as dates
    if images is None:
        images = [""] * len(dates)

    if dates == []:
        # Generate some suitable dates starting at the last existing entry
        conf = config.read_config(config_file)
        if conf is None:
            return 1
        dates = conf["dates"]
        if dates is None:
            # if there are no dates in the config, bail, something is wrong
            return 1
        sorted(dates, key=lambda x: x[0])
        last_day = datetime.datetime.strptime(dates[-1][0], "%Y%m%d")
        # Generate as many dates as we have images or just 1
        dates = [
            (last_day + datetime.timedelta(days=(i + 1))).strftime(
                "%Y%m%d",
            )
            for i in range(0, len(images))
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
    new_image: str | None,
    config_file: str,
) -> int:
    """
    Choose and move a new image to IMAGES
    """
    conf = config.read_config(config_file)
    if conf is None:
        return 1

    # Detect if a date or image has been used before
    for date, image in conf["dates"]:
        if date == new_date:
            print(f"Error: already have an image for {new_date}")
            return 1
        if new_image and image == new_image:
            print(f"Error: {new_image} was already used on {date}")
            return 1

    if new_image is None:
        new_image = random.choice(os.listdir(config.UNUSED_IMAGES))
    else:
        new_image = os.path.basename(new_image)

    old_image_path = os.path.join(config.UNUSED_IMAGES, new_image)
    if not os.path.exists(old_image_path):
        print(f"Error: {old_image_path} does not exist")
        return 1
    new_image_path = os.path.join(config.IMAGES, new_image)

    old_metadata_file = config.get_metadata_filename(
        config.UNUSED_METADATA,
        new_image,
    )
    if not os.path.exists(old_metadata_file):
        print(f"Error: {old_metadata_file} does not exist")
        return 1
    new_metadata_file = config.get_metadata_filename(
        config.METADATA_DIR,
        new_image,
    )

    print(f"Moving {old_image_path} to {new_image_path}")
    shutil.move(old_image_path, new_image_path)

    print(f"Moving {old_metadata_file} to {new_metadata_file}")
    shutil.move(old_metadata_file, new_metadata_file)

    conf["dates"].append([new_date, new_image])
    print(f"Writing {config_file}")
    with open(config_file, "w") as c:
        json.dump(conf, c, sort_keys=True, indent=2)
        # json module doesn't write a trailing newline by default
        c.write(os.linesep)

    print(f"Added {new_date}: {new_image}")
    return 0
