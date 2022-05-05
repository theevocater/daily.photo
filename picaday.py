#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import shutil
import string
from typing import List
from typing import Optional
from typing import TypedDict


def format_filename(output_dir: str, day: datetime.datetime) -> str:
    return os.path.join(output_dir, f'{day.strftime("%Y%m%d")}.html')


YESTERDAY_ANCHOR = '<a href="{}">&lt;-</a>'
TOMORROW_ANCHOR = '<a href="{}">-&gt;</a>'


class TemplateSubstitutions(TypedDict):
    yesterday: str
    tomorrow: str
    image: str
    alt: str
    subtitle: str


def generate_html(
    template_filename: str,
    data: TemplateSubstitutions,
    output_filename: str,
) -> None:
    with open(template_filename) as f:
        daily_template = string.Template(''.join(f.readlines()))

    # TODO check that this fully substituted or use better templating
    html_content = daily_template.substitute(data)

    with open(output_filename, 'w') as f:
        f.write(html_content)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='generate todays pic site')
    parser.add_argument('image', help='image to use instead of random')
    parser.add_argument(
        '--template',
        default='template.html',
        help='html template file',
    )
    parser.add_argument('--day', help='day in YYYMMDD format to generate')
    parser.add_argument(
        '--index',
        action='store_true',
        help='Generate index.html instead of day.html',
    )
    parser.add_argument(
        '--no-next',
        action='store_true',
        help='Dont add a next arrow',
    )
    parser.add_argument(
        '--no-prev',
        action='store_true',
        help='Dont add a back arrow',
    )
    args = parser.parse_args(argv)

    output_dir = 'docs'

    image = args.image
    if args.day:
        today = datetime.datetime.strptime(args.day, '%Y%m%d')
    else:
        today = datetime.datetime.now()

    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)

    metadata_file = os.path.splitext(image)[0] + '.json'

    with open(metadata_file) as f:
        metadata = json.load(f)

    yesterday_text = (
        '&lt;-'
        if args.no_prev
        else YESTERDAY_ANCHOR.format(
            format_filename('/', yesterday),
        )
    )

    if args.index:
        tomorrow_text = '-&gt;'
        output_name = os.path.join(output_dir, 'index.html')
    else:
        if args.no_next:
            tomorrow_text = TOMORROW_ANCHOR.format('/')
        else:
            tomorrow_text = TOMORROW_ANCHOR.format(
                format_filename('/', tomorrow),
            )
        output_name = format_filename(output_dir, today)

    generate_html(
        args.template,
        {
            'yesterday': yesterday_text,
            'tomorrow': tomorrow_text,
            'image': f'images/{os.path.basename(image)}',
            'alt': metadata['alt'],
            'subtitle': metadata['subtitle'],
        },
        output_name,
    )

    shutil.copy(image, os.path.join(output_dir, 'images/'))

    return 0


if __name__ == '__main__':
    exit(main())
