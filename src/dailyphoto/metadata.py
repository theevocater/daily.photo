import json
import os
import subprocess
import sys

from dailyphoto.validate import validate_metadata
from pydantic import ValidationError

from . import kitty
from .config import Config
from .config import MetadataEditable
from .config import read_metadata
from .config import write_metadata
from .exif import exif_to_metadata


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
    try:
        # TODO read_metadata needs to do a editable
        metadata = read_metadata(json_name, MetadataEditable) or MetadataEditable()
    except (json.decoder.JSONDecodeError, ValidationError) as e:
        # if the json is garbage, give it to me to edit it
        print(f"Unable to parse metadata file: {json_name}.", e)
        return edit_json(json_name, image_name, window_id)

    # create or fix the metadata dict with data from the image
    exif_to_metadata(image_name, metadata)
    write_metadata(json_name, metadata)

    # TODO i think we load as metadata here and go through the errors, but i think that means we can probably flip this function around asdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdf
    edit = always_edit or not validate_metadata(json_name, metadata)

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
        print(f"No need to edit {json_name}")
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
