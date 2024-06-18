#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys

METADATA_TEMPLATE = {
    "alt": "",
    "camera": "",
    "date": "",
    "film": "",
    "subtitle": "",
}


def edit_json(json_name: str) -> int:
    inp = input("s?")
    if inp == "s":
        return 0
    return subprocess.call(["vim", json_name])


def create_empty_metadata(json_name: str) -> bool:
    with open(json_name, "w") as f:
        json.dump(
            METADATA_TEMPLATE,
            f,
            sort_keys=True,
            indent=2,
        )
        f.write(os.linesep)
    return True


def update(
    image_name: str,
    json_name: str,
    always_edit: bool,
    fields: set[str] | None,
) -> int:
    if not os.path.exists(json_name):
        print("Creating missing {json_name}")
        create_empty_metadata(json_name)
    try:
        with open(json_name) as f:
            metadata = json.load(f)
    except FileNotFoundError as e:
        print(f"Unable to load metadata file: {json_name}.", e)
        return 1
    except json.decoder.JSONDecodeError as e:
        print(f"Unable to parse metadata file: {json_name}.", e)
        return edit_json(json_name)

    edit = always_edit
    for k, v in metadata.items():
        if edit:
            break
        if fields and k not in fields:
            continue
        if v == "":
            edit = True

    if edit:
        json.dump(
            metadata,
            sys.stdout,
            sort_keys=True,
            indent=2,
        )
        print()
        print(f"editing {os.path.basename(image_name)}")
        return edit_json(json_name)
    else:
        print(f"No need to edit {json_name}")
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
        "--always-edit",
        help="Comma separate list of fields to check if a file needs editing.",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--fields",
        help="Comma separate list of fields to check if a file needs editing.",
        default=None,
    )
    parser.add_argument(
        "source_dir",
        help="Source directory for images",
    )
    args = parser.parse_args(argv)
    fields = args.fields.split(",") if args.fields else None
    OUTPUT_DIR = args.source_dir
    IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")
    METADATA_DIR = os.path.join(OUTPUT_DIR, "metadata")
    rets = 0
    for file in os.listdir(IMAGE_DIR):
        prefix, ext = os.path.splitext(file)
        if ext == ".jpg":
            rets += update(
                os.path.join(IMAGE_DIR, file),
                os.path.join(METADATA_DIR, prefix + os.path.extsep + "json"),
                args.always_edit,
                fields,
            )

    return 0


if __name__ == "__main__":
    exit(main())
