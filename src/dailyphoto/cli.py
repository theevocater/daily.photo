import argparse
import logging

from . import config
from .exif import print_exif
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
    parser.add_argument(
        "--verbose",
        help="Set log level to info",
        action="store_true",
    )
    subparsers = parser.add_subparsers(dest="function")
    sp = subparsers.add_parser(
        "generate",
        help="default: Generate static site suitable for gh pages",
    )
    sp.add_argument("--no-tar", default=True, dest="tar", action="store_false", help="Disable creation of tarball")

    sp = subparsers.add_parser(
        "new",
        help=f"choose and add new image from {config.UNUSED_IMAGES} for YYYYMMDD",
    )
    sp.add_argument(
        "--dates",
        nargs="*",
        help="optional. list of YYYYMMDD to add new images",
    )
    sp.add_argument(
        "--images",
        nargs="*",
        help="optional. list of specific images instead of random",
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

    sp = subparsers.add_parser(
        "exif",
        help="Print EXIF data for a specified JPG file",
    )
    sp.add_argument(
        "images",
        help="Path to the image(s)",
        nargs="*",
    )

    sp = subparsers.add_parser(
        "watch",
        help="Watch [path] for changes and generate",
    )
    sp.add_argument(
        "path",
        help="Path to watch",
        default=".",
    )

    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

    conf = config.read_config(args.config_file)
    if conf is None:
        return 1

    if args.function == "new":
        return new(
            images=args.images,
            dates=args.dates,
            config_file=args.config_file,
        )
    elif args.function == "validate":
        return validate(conf=conf)
    elif args.function == "metadata":
        return metadata(
            conf=conf,
            always_edit=args.always_edit,
            source_dir=args.source_dir,
        )
    elif args.function == "queue":
        return queue_images(
            conf=conf,
            source_dir=args.source_dir,
        )
    elif args.function == "exif":
        return print_exif(args.images)
    elif args.function == "generate":
        return generate(conf=conf, tar=args.tar)
    elif args.function == "watch":
        try:
            from dailyphoto.watch import watch

            return watch(conf=conf, path=args.path)
        except ImportError:
            print("Watch unavaiable without watchdog module")
            return 1
    else:
        parser.parse_args(["-h"])
        return 1
