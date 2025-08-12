import datetime
import html
import os
import shutil
import string
import sys
import tarfile
from typing import TypedDict

from .config import Config
from .config import IMAGES
from .config import METADATA_DIR
from .config import OUTPUT_DIR
from .config import OUTPUT_IMAGES
from .config import TEMPLATE
from .metadata import get_metadata_filename
from .metadata import read_metadata

RSS_FEED_HEADER = """\
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Daily Photo</title>
  <link rel="self" href="https://daily.photo"/>
  <updated>{date}</updated>
  <author>
    <name>Jake Kaufman</name>
    <email>me@jake.computer</email>
  </author>
  <id>https://daily.photo/</id>
"""

RSS_FEED_ENTRY = """
  <entry>
    <title>{title}</title>
    <link href="{link}"/>
    <id>{link}</id>
    <summary type="xhtml">
      <div xmlns="http://www.w3.org/1999/xhtml">
        <div><img src="{img_link}" title="{alt}" alt="{alt}" /></div>
        <p>"{subtitle}"</p>
      </div>
    </summary>
    <updated>{date}</updated>
  </entry>
"""

RSS_FEED_TRAILER = "\n</feed>\n"


def format_filename(output_dir: str, day: datetime.datetime) -> str:
    return os.path.join(output_dir, f"{day.strftime('%Y%m%d')}.html")


# TODO convert to pydantic and align template with existing types
class TemplateSubstitutions(TypedDict):
    yesterday: str
    tomorrow: str
    image: str
    alt: str
    subtitle: str
    date: str
    shot_date: str
    camera: str
    film: str


def generate_html(
    template_filename: str,
    data: TemplateSubstitutions,
    output_filename: str,
) -> None:
    with open(template_filename) as f:
        daily_template = string.Template("".join(f.readlines()))

    # TODO check that this fully substituted or use better templating
    html_content = daily_template.substitute(data)

    with open(output_filename, "w") as f:
        f.write(html_content)


def photo_date(date: datetime.datetime) -> str:
    return date.strftime("%B %d, %Y")


def rss_date(date: datetime.datetime) -> str:
    """
    Return a ISO3601 UTC date without external library
    """
    return date.isoformat() + "Z"


def is_final_day(conf: Config, day: datetime.datetime) -> bool:
    return day == conf.dates[-1].day


def generate_day(
    *,
    conf: Config,
    prev_day: datetime.datetime,
    current_day: datetime.datetime,
    next_day: datetime.datetime,
    image: str,
    metadata_file: str,
    template: str,
    index: bool,
    output_dir: str,
) -> str:
    if index:
        output_name = os.path.join(output_dir, "index.html")
    else:
        output_name = format_filename(output_dir, current_day)

    print(f"Generating {output_name}")

    metadata = read_metadata(metadata_file)
    if metadata is None:
        print(f"Unable to parse {metadata_file} date: {current_day}")
        # TODO: error handling shouldn't be immediate exit. need to better
        # collect and bubble errors
        sys.exit(1)

    # symlink this days image to the output directory
    intput_image = os.path.join("..", "..", IMAGES, image)
    output_image = os.path.join(output_dir, OUTPUT_IMAGES, image)
    if not os.path.exists(output_image):
        if os.path.lexists(output_image):
            # fix broken links
            os.remove(output_image)
        os.symlink(intput_image, output_image)

    tomorrow = format_filename("/", next_day)
    if is_final_day(conf, next_day):
        tomorrow = "index.html"

    generate_html(
        template,
        {
            "yesterday": format_filename("/", prev_day),
            "tomorrow": tomorrow,
            "image": os.path.join(OUTPUT_IMAGES, image),
            "alt": metadata.alt,
            "subtitle": metadata.subtitle,
            "date": current_day.strftime("%B %d, %Y"),
            "shot_date": photo_date(metadata.date),
            "camera": metadata.camera,
            "film": metadata.film,
        },
        output_name,
    )

    if index:
        # index isn't included in the RSS feed
        return ""

    return RSS_FEED_ENTRY.format(
        title=metadata.subtitle,
        link=f"https://daily.photo/{current_day.strftime('%Y%m%d')}.html",
        date=rss_date(current_day),
        alt=html.escape(metadata.alt),
        img_link=f"https://daily.photo/{OUTPUT_IMAGES}/{image}",
        subtitle=html.escape(metadata.subtitle),
    )


def setup_output_dir(output_dir: str) -> bool:
    """
    Creates the output dir and links base files like CSS
    """
    # clear out previous dir if it exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    print(f"Creating {output_dir}")
    os.mkdir(output_dir)

    images = os.path.join(output_dir, OUTPUT_IMAGES)
    if not os.path.exists(images):
        print(f"Creating {images}")
        os.mkdir(images)

    main_css = f"{output_dir}/main.css"
    if not os.path.exists(main_css):
        print(f"Creating {main_css}")
        os.symlink("../main.css", main_css)

    main_js = f"{output_dir}/main.js"
    if not os.path.exists(main_js):
        print(f"Creating {main_js}")
        os.symlink("../main.js", main_js)

    return True


def create_tar_gz_with_symlinks(source_dir: str, output_filename: str) -> None:
    """
    Creates a tar.gz archive of the given directory.
    Resolve symlinks to their target.
    """
    # remove old tar file
    if os.path.exists(output_filename):
        os.remove(output_filename)

    with tarfile.open(output_filename, "w:gz") as tar:
        for root, _, files in os.walk(source_dir):
            for name in files:
                full_path = os.path.join(root, name)
                # Resolve symlinks to their targets
                if os.path.islink(full_path):
                    target_path = os.path.realpath(full_path, strict=True)
                    tar.add(
                        target_path,
                        arcname=os.path.relpath(full_path, start=source_dir),
                    )
                else:
                    tar.add(
                        full_path,
                        arcname=os.path.relpath(full_path, start=source_dir),
                    )


def generate(*, conf: Config) -> int:
    print("Generating site")
    if not setup_output_dir(OUTPUT_DIR):
        return 1

    rss_feed = RSS_FEED_HEADER.format(
        date=rss_date(datetime.datetime.now()),
    )

    dates = conf.dates
    for i, date in enumerate(dates):
        today = date.day
        metadata_file = get_metadata_filename(
            METADATA_DIR,
            date.filename,
        )

        # Determine previous, current, and next days
        if i == 0:
            prev_day = today
        else:
            prev_day = dates[i - 1].day

        if i == len(dates) - 1:
            next_day = today
        else:
            next_day = dates[i + 1].day

        if i == len(dates) - 1:
            # Last day we need to generate the index and no anchor
            generate_day(
                conf=conf,
                prev_day=prev_day,
                current_day=today,
                next_day=next_day,
                image=date.filename,
                index=True,
                metadata_file=metadata_file,
                template=TEMPLATE,
                output_dir=OUTPUT_DIR,
            )

        rss_feed += generate_day(
            conf=conf,
            prev_day=prev_day,
            current_day=today,
            next_day=next_day,
            image=date.filename,
            index=False,
            metadata_file=metadata_file,
            template=TEMPLATE,
            output_dir=OUTPUT_DIR,
        )

    rss_feed += RSS_FEED_TRAILER
    rss_file = os.path.join(OUTPUT_DIR, "rss.xml")
    print(f"Writing {rss_file}")
    with open(rss_file, "w") as rss:
        rss.write(rss_feed)

    create_tar_gz_with_symlinks(OUTPUT_DIR, "dailyphoto.tar.gz")
    return 0
