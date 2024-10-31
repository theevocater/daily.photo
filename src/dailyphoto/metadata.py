import json
import os
import subprocess
import sys

from . import kitty

METADATA_TEMPLATE = {
    "alt": "",
    "camera": "",
    "date": "",
    "film": "",
    "subtitle": "",
}


def edit_json(json_name: str, image_name: str, window_id: str) -> int:
    inp = input("sq?")
    if inp == "s":
        return 0
    if inp == "q":
        return -1
    kitty.open_image(image_name, window_id)

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
    window_id: str,
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
        return edit_json(json_name, image_name, window_id)

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
        return edit_json(json_name, image_name, window_id)
    else:
        print(f"No need to edit {json_name}")
        return 0


def metadata(
    *,
    always_edit: bool,
    fields_csv: str | None,
    source_dir: str,
) -> int:
    fields = set(fields_csv.split(",")) if fields_csv else None

    id = kitty.new_window()

    output_dir = source_dir
    image_dir = os.path.join(output_dir, "images")
    metadata_dir = os.path.join(output_dir, "metadata")
    rets = 0
    for file in os.listdir(image_dir):
        prefix, ext = os.path.splitext(file)
        if ext == ".jpg":
            ret = update(
                os.path.join(image_dir, file),
                os.path.join(metadata_dir, prefix + os.path.extsep + "json"),
                always_edit,
                id,
                fields,
            )
            # -1 is the signal to quit since processes return positive numbers
            if ret < 0:
                break
            rets += ret
    kitty.close_window(id)
    return rets
