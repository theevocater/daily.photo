import json
import os
import subprocess
import sys

from pydantic import ValidationError

from . import kitty
from .config import Config
from .exif import exif_to_metadata
from .types import Metadata
from .types import MetadataEditable


def get_metadata_filename(metadata_dir: str, image: str) -> str:
    return os.path.join(
        metadata_dir,
        os.path.splitext(os.path.basename(image))[0] + ".json",
    )


def read_metadata(metadata_file: str) -> Metadata | None:
    try:
        with open(metadata_file) as c:
            parsed = json.load(c)
            return Metadata.model_validate(parsed)
    except (FileNotFoundError, json.decoder.JSONDecodeError, ValidationError) as e:
        print(f"Unable to load metadata: {metadata_file}.", str(e))
        return None


def write_metadata(metadata_file: str, metadata: Metadata | MetadataEditable) -> None:
    try:
        with open(metadata_file, "w") as c:
            c.write(metadata.model_dump_json(indent=2))
            # include a final line ending
            c.write("\n")
    except OSError as e:
        print(f"Unable to write metadata: {metadata_file}.", e)


def edit_json(json_name: str, image_name: str, window_id: str) -> int:
    inp = input("[e]dit,[s]kip,[q]uit?")
    if inp == "s":
        return 0
    if inp == "q":
        return -1
    kitty.open_image(image_name, window_id)

    return subprocess.call(["nvim", json_name])


def update(
    image_name: str,
    json_name: str,
    always_edit: bool,
    window_id: str,
) -> int:
    # First attempt to validate the existing on disk metadata file to see if it needs edited.
    edit = always_edit
    json_dict = None
    try:
        with open(json_name) as c:
            json_dict = json.load(c)
    except FileNotFoundError:
        print(f"Creating new metadata {json_name}.")
        edit = True
    except json.decoder.JSONDecodeError as e:
        # if the json is garbage just to edit it
        print(f"Unable to parse metadata file: {json_name}.", e)
        return edit_json(json_name, image_name, window_id)

    metadata = MetadataEditable()
    if json_dict is not None:
        try:
            Metadata.model_validate(json_dict)
        except ValidationError as valid_e:
            # If it fails to validate, we need to edit.
            print(f"Metadata file {json_name} failed to validate:")
            for x in valid_e.errors():
                print(f"\tField {x['loc'][0]}: {x['msg']}")
            edit = True

        # Load existing data
        metadata = metadata.model_validate(json_dict)

    # Update metadata with data from the image
    exif_to_metadata(image_name, metadata)
    write_metadata(json_name, metadata)

    if edit or always_edit:
        json.dump(
            metadata.model_dump(),
            sys.stdout,
            sort_keys=True,
            indent=2,
        )
        print()
        print(f"editing {os.path.basename(image_name)}")
        return edit_json(json_name, image_name, window_id)
    else:
        return 0


def metadata(
    *,
    conf: Config,
    always_edit: bool,
    source_dir: str,
) -> int:
    id = kitty.new_window()
    kitty.set_layout("horizontal")

    output_dir = source_dir
    image_dir = os.path.join(output_dir, "images")
    metadata_dir = os.path.join(output_dir, "metadata")
    rets = 0

    for date in conf.dates:
        prefix, ext = os.path.splitext(date.filename)
        if ext == ".jpg":
            ret = update(
                os.path.join(image_dir, date.filename),
                os.path.join(metadata_dir, prefix + os.path.extsep + "json"),
                always_edit,
                id,
            )
            # -1 is the signal to quit since processes return positive numbers
            if ret < 0:
                break
            rets += ret
    kitty.close_window(id)
    return rets
