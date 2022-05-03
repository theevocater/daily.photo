#!/usr/bin/env python3
import datetime
import os
import random
import string
from typing import List
from typing import Optional


def main(argv: Optional[List[str]] = None) -> int:
    unused_images = os.listdir('unused/')
    image = unused_images[random.randint(0, len(unused_images))]

    with open('template.html') as f:
        daily_template = string.Template(''.join(f.readlines()))

    output_name = ''.join((
        'html/',
        datetime.datetime.now().strftime('%Y%m%d'),
        '.html',
    ))

    with open(output_name, 'w') as f:
        f.write(
            daily_template.substitute(
                {
                    'image_path': f'/used/{image}',
                    'alt': 'woo',
                    'subtitle': 'Test 123',
                },
            ),
        )

    os.rename(f'unused/{image}', f'used/{image}')
    return 0


if __name__ == '__main__':
    exit(main())
