import argparse

from . import config
from .generate import generate
from .metadata import metadata
from .new import new
from .queued import queue_images
from .validate import validate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="generate todays pic site")
    parser.add_argument(
        "--config-file",
        help="Path to config file. defaults to ./config.json",
        default="config.json",
    )
    subparsers = parser.add_subparsers(dest="function")
    sp = subparsers.add_parser(
        "generate",
        help="default: Generate static site suitable for gh pages",
    )

    sp = subparsers.add_parser(
        "new",
        help=f"choose and add new image from {
            config.UNUSED_IMAGES
        } for YYYYMMDD",
    )
    sp.add_argument(
        "date",
        nargs="*",
        help="YYYYMMDD to add new image",
    )
    sp.add_argument(
        "--image",
        dest="image",
        nargs="*",
        help="optional. if passed, use a specific image instead of random",
    )

    sp = subparsers.add_parser(
        "validate",
        help="validate config.json",
    )
    sp = subparsers.add_parser(
        "metadata",
        help="Update image metadata alongside the image",
    )
    sp.add_argument(
        "--always-edit",
        help="Don't ask before editing the metadata.",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    sp.add_argument(
        "--fields",
        help="Comma separate list of fields to check if a file needs editing.",
        default=None,
    )
    sp.add_argument(
        "source_dir",
        help="Source directory for images",
    )
    sp = subparsers.add_parser(
        "queue",
        help="Queue new images",
    )
    sp.add_argument(
        "source_dir",
        help="Source directory for images",
    )
    args = parser.parse_args(argv)

    if args.function == "new":
        return new(
            images=args.image,
            dates=args.date,
            config_file=args.config_file,
        )
    elif args.function == "validate":
        return validate(config_file=args.config_file)
    elif args.function == "metadata":
        return metadata(
            always_edit=args.always_edit,
            fields_csv=args.fields,
            source_dir=args.source_dir,
        )
    elif args.function == "queue":
        return queue_images(
            config_file=args.config_file,
            source_dir=args.source_dir,
        )
    else:
        return generate(config_file=args.config_file)
