#!/usr/bin/env python3
import argparse
import base64
import datetime
import json
import os
import random
import string
from typing import List
from typing import Optional


def choose_image() -> str:
    unused_images = os.listdir('unused/')
    return unused_images[random.randint(0, len(unused_images))]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='generate todays pic site')
    parser.add_argument('image', help='image to use instead of random')
    parser.add_argument(
        '--template', default='template.html',
        help='html template file',
    )
    args = parser.parse_args(argv)

    # TODO harmonize this naming stuff
    image = os.path.basename(args.image) or choose_image()

    with open(args.template) as f:
        daily_template = string.Template(''.join(f.readlines()))

    output_name = ''.join((
        'html/',
        datetime.datetime.now().strftime('%Y%m%d'),
        '.html',
    ))
    metadata_file = os.path.join(
        'unused',
        os.path.splitext(image)[0] + '.json',
    )
    with open(metadata_file) as f:
        metadata = json.load(f)

    with open(f'used/{image}', 'rb') as b:
        image_b64 = base64.b64encode(b.read()).decode('utf-8')

    image_b64 = f'data:image/jpg;base64,{image_b64}'

    with open(output_name, 'w') as f:
        f.write(
            daily_template.substitute(
                {
                    'image': image_b64,
                    'alt': metadata['alt'],
                    'subtitle': metadata['subtitle'],
                },
            ),
        )

    if os.path.exists(f'unused/{image}'):
        os.rename(f'unused/{image}', f'used/{image}')

    return 0


if __name__ == '__main__':
    exit(main())
