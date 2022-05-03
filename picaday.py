#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import shutil
import string
from typing import List
from typing import Optional


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='generate todays pic site')
    parser.add_argument('image', help='image to use instead of random')
    parser.add_argument(
        '--template', default='template.html',
        help='html template file',
    )
    args = parser.parse_args(argv)

    image = args.image

    with open(args.template) as f:
        daily_template = string.Template(''.join(f.readlines()))

    output_name = ''.join((
        'site/',
        datetime.datetime.now().strftime('%Y%m%d'),
        '.html',
    ))
    metadata_file = os.path.splitext(image)[0] + '.json'

    with open(metadata_file) as f:
        metadata = json.load(f)

    html_content = daily_template.substitute(
        {
            'image': f'images/{os.path.basename(image)}',
            'alt': metadata['alt'],
            'subtitle': metadata['subtitle'],
        },
    )

    with open(output_name, 'w') as f:
        f.write(html_content)

    with open('site/index.html', 'w') as f:
        f.write(html_content)

    shutil.copy(image, 'site/images/')

    return 0


if __name__ == '__main__':
    exit(main())
