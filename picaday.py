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

    # TODO this code is bad
    yesterday_text = format_filename(output_dir, yesterday)
    if os.path.exists(yesterday_text):
        with open(yesterday_text) as f:
            lines: List[str] = []
            for line in f:
                lines += line.replace('index.html', format_filename('', today))
        with open(yesterday_text, 'w') as f:
            f.write(''.join(lines))
        yesterday_text = format_filename('/', yesterday)
    else:
        yesterday_text = format_filename('/', today)

    tomorrow_text = format_filename(output_dir, tomorrow)
    if os.path.exists(tomorrow_text):
        with open(tomorrow_text) as f:
            lines = []
            for line in f:
                lines += line.replace(
                    format_filename(
                        '/',
                        tomorrow,
                    ),
                    format_filename('/', today),
                )
        with open(tomorrow_text, 'w') as f:
            f.write(''.join(lines))
        tomorrow_text = format_filename('/', tomorrow)
    else:
        tomorrow_text = 'index.html'

    if args.index:
        output_name = os.path.join(output_dir, 'index.html')
    else:
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
