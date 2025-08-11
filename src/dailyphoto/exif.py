from datetime import datetime

from PIL import Image
from PIL.ExifTags import Base
from PIL.ExifTags import TAGS

from .types import MetadataEditable


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


def exif_to_metadata(image_file: str, metadata: MetadataEditable) -> None:
    with Image.open(image_file) as image:
        exif_data = image.getexif()
    if exif_data is None:
        return
    make = exif_data.get(Base["Make"])
    model = exif_data.get(Base["Model"])
    ifd_tags = exif_data.get_ifd(Image.ExifTags.IFD.Exif)
    dto = ifd_tags.get(Base["DateTimeOriginal"])
    exif_date = None
    if dto:
        exif_date = datetime.strptime(dto, "%Y:%m:%d %H:%M:%S") or None

    if make and model and metadata.camera == "":
        metadata.camera = f"{make} {model}"
    # Always trust the camera for digital cameras
    if exif_date and make == "FUJIFILM":
        metadata.date = exif_date
    # seed the date if we don't have one at all
    elif exif_date and not metadata.date:
        metadata.date = exif_date
