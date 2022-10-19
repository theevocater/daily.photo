#!/usr/bin/env python3
import json
import os
import subprocess
from typing import List
from typing import Optional

METADATA_TEMPLATE = {
    'alt': '',
    'camera': '',
    'date': '',
    'film': '',
    'subtitle': '',
}


def edit_json(json_name: str) -> int:
    return subprocess.call(['vim', json_name])


def create_empty_metadata(json_name: str) -> bool:
    with open(json_name, 'w') as f:
        json.dump(
            METADATA_TEMPLATE,
            f,
            sort_keys=True,
            indent=2,
        )
        f.write(os.linesep)
    return True


def update(image_name: str, json_name: str) -> int:
    if not os.path.exists(json_name):
        print('Creating missing {json_name}')
        create_empty_metadata(json_name)
    with open(json_name) as f:
        metadata = json.load(f)
    edit = False
    for k, v in metadata.items():
        if v == '':
            edit = True
    if edit:
        print(f'editing {os.path.basename(image_name)}')
        input()
        return edit_json(json_name)
    else:
        print(f'No need to edit {json_name}')
        return 0


def main(argv: Optional[List[str]] = None) -> int:
    rets = 0
    for file in os.listdir('converted/'):
        prefix, ext = os.path.splitext(file)
        if ext == '.jpg':
            rets += update(
                os.path.join('converted', file),
                os.path.join('converted', prefix + os.path.extsep + 'json'),
            )

    return 0


if __name__ == '__main__':
    exit(main())
