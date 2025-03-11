from datetime import datetime

from PIL import Image
from PIL.ExifTags import Base
from PIL.ExifTags import TAGS


def print_exif(image_files: list[str]) -> int:
    for image in image_files:
        try:
            with Image.open(image) as img:
                exif_data = img.getexif()
                if exif_data is not None:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        print(f"{tag}: {value}")
                    for tag_id, value in exif_data.get_ifd(
                        Image.ExifTags.IFD.Exif,
                    ).items():
                        tag = TAGS.get(tag_id, tag_id)
                        print(f"{tag}: {value}")
                else:
                    print(f"No EXIF data found for {image}.")
        except Exception as e:
            print(f"Error reading EXIF data from {image}: {e}")
    return 0


def exif_to_metadata(image_file: str, metadata: dict[str, str]) -> None:
    exif_tags: dict[str, str | None] = {
        "Make": None,
        "Model": None,
        "DateTime": None,
    }

    with Image.open(image_file) as image:
        exif_data = image.getexif()
        if exif_data is not None:
            for tag in exif_tags.keys():
                exif_tags[tag] = exif_data.get(Base[tag])
    if exif_tags["Make"] and exif_tags["Model"] and metadata["camera"] == "":
        metadata["camera"] = f"{exif_tags['Make']} {exif_tags['Model']}"
    if exif_tags["DateTime"] and metadata["date"] == "":
        metadata["date"] = datetime.strftime(
            datetime.strptime(exif_tags["DateTime"], "%Y:%m:%d %H:%M:%S"),
            "%Y%m%d",
        )
