import datetime
import logging
import os
import shutil
import sys
import tarfile
from typing import Annotated

from dailyphoto.types import Metadata
from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape
from pydantic import BaseModel
from pydantic import PlainSerializer

from .config import Config
from .config import IMAGES
from .config import METADATA_DIR
from .config import OUTPUT_DIR
from .config import OUTPUT_IMAGES
from .metadata import get_metadata_filename
from .metadata import read_metadata

logger = logging.getLogger(__name__)


def format_filename(output_dir: str, day: datetime.datetime) -> str:
    return os.path.join(output_dir, f"{day.strftime('%Y%m%d')}.html")


class DailyTemplate(BaseModel):
    date: datetime.datetime
    yesterday: str
    tomorrow: str
    image: str
    metadata: Metadata


class MonthlyImage(BaseModel):
    link: str
    file: str
    alt: str


def monthly_filename(month: datetime.datetime | None) -> str:
    if month is None:
        return ""
    return f"{month.year}-{month.month}.html"


class MonthlyTemplate(BaseModel):
    month: datetime.datetime
    prev: Annotated[datetime.datetime | None, PlainSerializer(monthly_filename)] = None
    next: Annotated[datetime.datetime | None, PlainSerializer(monthly_filename)] = None
    images: list[MonthlyImage]


def rss_date(date: datetime.datetime) -> str:
    """
    Return a ISO3601 UTC date without external library
    """
    return date.isoformat() + "Z"


class RSSEntry(BaseModel):
    title: str
    link: str
    img_link: str
    alt: str
    subtitle: str
    date: str


class RSSFeed(BaseModel):
    date: Annotated[datetime.datetime, PlainSerializer(rss_date)]
    entries: list[RSSEntry]


def photo_date(date: datetime.datetime) -> str:
    return date.strftime("%B %d, %Y")


def generate_day(
    *,
    env: Environment,
    conf: Config,
    prev_day: datetime.datetime,
    current_day: datetime.datetime,
    next_day: datetime.datetime,
    image: str,
    metadata_file: str,
    index: bool,
    output_dir: str,
    rss_feed: RSSFeed,
    month: MonthlyTemplate,
) -> None:
    if index:
        output_name = os.path.join(output_dir, "index.html")
    else:
        output_name = format_filename(output_dir, current_day)

    logger.info(f"Generating {output_name}")

    metadata = read_metadata(metadata_file)
    if metadata is None:
        logger.error(f"Unable to parse {metadata_file} date: {current_day}")
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
    if next_day == conf.dates[-1].day:
        tomorrow = "index.html"

    html_content = env.get_template("template.html").render(
        DailyTemplate(
            date=current_day,
            yesterday=format_filename("/", prev_day),
            tomorrow=tomorrow,
            image=os.path.join(OUTPUT_IMAGES, image),
            metadata=metadata,
        ),
    )
    with open(output_name, "w") as f:
        f.write(html_content)

    if index:
        # index isn't included in the RSS feed
        return

    month.images.append(
        MonthlyImage(
            link=format_filename("/", current_day),
            file=os.path.join(OUTPUT_IMAGES, image),
            alt=metadata.alt,
        ),
    )

    rss_feed.entries.append(
        RSSEntry(
            title=metadata.subtitle,
            link=f"https://daily.photo/{current_day.strftime('%Y%m%d')}.html",
            date=rss_date(current_day),
            alt=metadata.alt,
            img_link=f"https://daily.photo/{OUTPUT_IMAGES}/{image}",
            subtitle=metadata.subtitle,
        ),
    )


def setup_output_dir(env: Environment, output_dir: str) -> bool:
    """
    Creates the output dir and links base files like CSS
    """
    # clear out previous dir if it exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    logger.info(f"Creating {output_dir}")
    os.mkdir(output_dir)

    images = os.path.join(output_dir, OUTPUT_IMAGES)
    if not os.path.exists(images):
        logger.info(f"Creating {images}")
        os.mkdir(images)

    untemplated_files = [
        "main.css",
        "main.js",
        "month.css",
    ]

    for file in untemplated_files:
        filename = f"{output_dir}/{file}"
        with open(filename, "w") as f:
            logger.info(f"Creating {filename}")
            f.write(env.get_template(file).render())

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


def generate(*, conf: Config, tar: bool) -> int:
    env = Environment(loader=PackageLoader("dailyphoto", "resources"), autoescape=select_autoescape(["html", "xml"]))

    logger.info("Generating site")
    if not setup_output_dir(env, OUTPUT_DIR):
        return 1

    rss_feed = RSSFeed(date=datetime.datetime.now(), entries=[])

    dates = conf.dates
    month = MonthlyTemplate(month=dates[0].day, images=[])
    for i, date in enumerate(dates):
        today = date.day
        curr_month = datetime.datetime(year=today.year, month=today.month, day=1)
        if curr_month != month.month:
            # New month, write and reset
            month.next = curr_month
            monthly_file = os.path.join(OUTPUT_DIR, monthly_filename(month.month))
            logger.info(f"Writing {monthly_file}")
            with open(monthly_file, "w") as rss:
                rss.write(env.get_template("month.html").render(month.model_dump()))
            month = MonthlyTemplate(month=today, prev=month.month, images=[])

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
                env=env,
                conf=conf,
                prev_day=prev_day,
                current_day=today,
                next_day=next_day,
                image=date.filename,
                index=True,
                metadata_file=metadata_file,
                output_dir=OUTPUT_DIR,
                rss_feed=rss_feed,
                month=month,
            )

        generate_day(
            env=env,
            conf=conf,
            prev_day=prev_day,
            current_day=today,
            next_day=next_day,
            image=date.filename,
            index=False,
            metadata_file=metadata_file,
            output_dir=OUTPUT_DIR,
            rss_feed=rss_feed,
            month=month,
        )

    monthly_file = monthly_filename(month.month)
    logger.info(f"Writing {monthly_file}")
    with open(monthly_file, "w") as rss:
        rss.write(env.get_template("month.html").render(month.model_dump()))

    rss_file = os.path.join(OUTPUT_DIR, "rss.xml")
    logger.info(f"Writing {rss_file}")
    with open(rss_file, "w") as rss:
        rss.write(env.get_template("rss.xml").render(rss_feed.model_dump()))

    if tar:
        create_tar_gz_with_symlinks(OUTPUT_DIR, "dailyphoto.tar.gz")
    return 0
