#!/usr/bin/env python3
import argparse
import datetime
import json
import os
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
    date: str
    camera: str
    film: str


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


def photo_date(date: str) -> str:
    if not date:
        return ''
    return datetime.datetime.strptime(date, '%Y%m%d').strftime('%B %d, %Y')


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='generate todays pic site')
    parser.add_argument('image', help='image to use instead of random')
    parser.add_argument(
        '--template',
        default='template.html',
        help='html template file'
    )
    parser.add_argument(
        '--metadata',
        help='image metadata json. defaults to metadata/imagename.json'
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

    metadata_file = args.metadata or os.path.join(
        'metadata',
        os.path.splitext(os.path.basename(image))[0] + '.json',
    )

    with open(metadata_file) as f:
        metadata = json.load(f)

    if args.no_prev:
        yesterday_text = '&lt;-'
    else:
        yesterday_text = '<a href="{}">&lt;-</a>'.format(
            format_filename('/', yesterday),
        )

    if args.no_next or args.index:
        tomorrow_text = '-&gt;'
    else:
        tomorrow_text = '<a href="{}">-&gt;</a>'.format(
            format_filename('/', tomorrow),
        )

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
            'date': photo_date(metadata.get('date', '')),
            'camera': metadata.get('camera', ''),
            'film': metadata.get('film', ''),
        },
        output_name,
    )

    return 0


if __name__ == '__main__':
    exit(main())
