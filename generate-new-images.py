#!/usr/bin/env python3
import argparse
import json
import os
import shutil

METADATA_TEMPLATE = {
    "alt": "",
    "camera": "",
    "date": "",
    "film": "",
    "subtitle": "",
}

OUTPUT_DIR = "queued"
IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")
METADATA_DIR = os.path.join(OUTPUT_DIR, "metadata")


def unused(dates: list[tuple[str, str]], new_image: str) -> bool:
    for date, image in dates:
        if image == new_image:
            print(f"{image} is already used on {date}")
            return False
        if os.path.exists(os.path.join(IMAGE_DIR, new_image)):
            print(f"{new_image} is already in {IMAGE_DIR}")
            return False
    return True


def write_metadata(json_name: str) -> int:
    print(f"Creating {json_name}")
    try:
        with open(json_name, "w") as f:
            json.dump(
                METADATA_TEMPLATE,
                f,
                sort_keys=True,
                indent=2,
            )
            f.write(os.linesep)
    except (
        FileNotFoundError,
        json.decoder.JSONDecodeError,
    ) as e:
        print(
            f"Unable to write metadata: {json_name}.",
            e,
        )
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="copy and create metadata files for new images",
    )
    parser.add_argument(
        "--config-file",
        help="Path to config file. defaults to ./config.json",
        default="config.json",
    )
    parser.add_argument(
        "source_dir",
        help="Source directory for images",
    )
    args = parser.parse_args(argv)
    try:
        with open(args.config_file) as c:
            config = json.load(c)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        print(f"Unable to load config_file: {args.config_file}.", e)
        return 1

    dates = config.get("dates", None)
    if dates is None:
        print("Unable to get dates from config")
        return 1

    if not os.path.exists(args.source_dir):
        print(f"Error: unable to list {args.source_dir}")
        return 1
    with os.scandir(args.source_dir) as it:
        for entry in it:
            if entry.is_file():
                name = entry.name
                prefix, ext = os.path.splitext(name)
                if ext == ".jpg" and unused(dates, name):
                    print(
                        f"Moving {
                            args.source_dir
                        }/{name} "
                        f"to {IMAGE_DIR}/{name}",
                    )
                    shutil.move(
                        os.path.join(args.source_dir, name),
                        os.path.join(IMAGE_DIR, name),
                    )
                    ret = write_metadata(
                        os.path.join(
                            METADATA_DIR,
                            prefix + os.path.extsep + "json",
                        ),
                    )
                    if ret != 0:
                        return ret

    return 0


if __name__ == "__main__":
    exit(main())
