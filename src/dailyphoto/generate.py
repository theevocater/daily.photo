import datetime
import json
import os
import string
import sys
from typing import TypedDict

from . import config

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
    <summary type="html">
        &lt;img src="{img_link}" title="{alt}" alt="{alt}" /&gt;
    </summary>
    <updated>{date}</updated>
  </entry>
"""

RSS_FEED_TRAILER = "\n</feed>\n"


def format_filename(output_dir: str, day: datetime.datetime) -> str:
    return os.path.join(output_dir, f"{day.strftime('%Y%m%d')}.html")


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


def photo_date(date: str) -> str:
    if not date:
        return ""
    return datetime.datetime.strptime(date, "%Y%m%d").strftime("%B %d, %Y")


def rss_date(date: datetime.datetime) -> str:
    """
    Return a ISO3601 UTC date without external library
    """
    return date.isoformat() + "Z"


def generate_day(
    *,
    today: datetime.datetime,
    image: str,
    metadata_file: str,
    template: str,
    index: bool,
    no_next: bool,
    no_prev: bool,
    output_dir: str,
) -> str:
    if index:
        output_name = os.path.join(output_dir, "index.html")
    else:
        output_name = format_filename(output_dir, today)

    print(f"Generating {output_name}")

    with open(metadata_file) as f:
        metadata = json.load(f)

    # TODO get rid of the parallel index.html and the lastday.html. its
    # confusing
    yesterday = today - datetime.timedelta(days=1)
    if no_prev:
        yesterday = today
    yesterday_text = format_filename("/", yesterday)

    tomorrow = today + datetime.timedelta(days=1)
    if no_next or index:
        tomorrow = today
    tomorrow_text = format_filename("/", tomorrow)

    try:
        shot_date = photo_date(metadata.get("date"))
    except ValueError:
        print(f"Unable to parse {metadata_file} date: {metadata.get('date')}")
        # TODO: error handling shouldn't be immediate exit. need to better
        # collect and bubble errors
        sys.exit(1)

    # symlink this days image to the output directory
    intput_image = os.path.join("..", "..", config.IMAGES, image)
    output_image = os.path.join(output_dir, config.OUTPUT_IMAGES, image)
    if not os.path.exists(output_image):
        if os.path.lexists(output_image):
            # fix broken links
            os.remove(output_image)
        os.symlink(intput_image, output_image)

    generate_html(
        template,
        {
            "yesterday": yesterday_text,
            "tomorrow": tomorrow_text,
            "image": os.path.join(config.OUTPUT_IMAGES, image),
            "alt": metadata["alt"],
            "subtitle": metadata["subtitle"],
            "date": today.strftime("%B %d, %Y"),
            "shot_date": shot_date,
            "camera": metadata.get("camera", ""),
            "film": metadata.get("film", ""),
        },
        output_name,
    )

    if index:
        # index isn't included in the RSS feed
        return ""

    return RSS_FEED_ENTRY.format(
        title=metadata["subtitle"],
        link=f"https://daily.photo/{today.strftime('%Y%m%d')}.html",
        date=rss_date(today),
        alt=metadata["alt"],
        img_link=f"https://daily.photo/{config.OUTPUT_IMAGES}/{image}",
    )


def setup_output_dir(output_dir: str) -> bool:
    """
    Creates the output dir and links base files like CSS
    """
    if not os.path.exists(output_dir):
        print(f"Creating {output_dir}")
        os.mkdir(output_dir)

    images = os.path.join(output_dir, config.OUTPUT_IMAGES)
    if not os.path.exists(images):
        print(f"Creating {images}")
        os.mkdir(images)

    cname = f"{output_dir}/CNAME"
    if not os.path.exists(cname):
        print(f"Creating {cname}")
        os.symlink("../CNAME", cname)

    main_css = f"{output_dir}/main.css"
    if not os.path.exists(main_css):
        print(f"Creating {main_css}")
        os.symlink("../main.css", main_css)

    return True


def generate(
    *,
    config_file: str,
) -> int:
    conf = config.read_config(config_file)
    if conf is None:
        return 1

    print("Generating site")
    if not setup_output_dir(config.OUTPUT_DIR):
        return 1

    rss_feed = RSS_FEED_HEADER.format(
        date=rss_date(datetime.datetime.now()),
    )

    no_prev = True
    no_next = False
    for date, image in conf["dates"]:
        today = datetime.datetime.strptime(date, "%Y%m%d")
        metadata_file = config.get_metadata_filename(
            config.METADATA_DIR,
            image,
        )

        if conf["dates"][-1][0] == date:
            # Last day we need to generate the index and no anchor
            # The index isn't included in the RSS feed
            no_next = True
            generate_day(
                today=today,
                image=image,
                index=True,
                metadata_file=metadata_file,
                no_next=no_next,
                no_prev=no_prev,
                template=config.TEMPLATE,
                output_dir=config.OUTPUT_DIR,
            )

        rss_feed += generate_day(
            today=today,
            image=image,
            index=False,
            metadata_file=metadata_file,
            no_next=no_next,
            no_prev=no_prev,
            template=config.TEMPLATE,
            output_dir=config.OUTPUT_DIR,
        )

        if no_prev:
            # only true on first go around
            no_prev = False

    rss_feed += RSS_FEED_TRAILER
    rss_file = os.path.join(config.OUTPUT_DIR, "rss.xml")
    print(f"Writing {rss_file}")
    with open(rss_file, "w") as rss:
        rss.write(rss_feed)

    return 0
