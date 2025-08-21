import logging
import time

from dailyphoto.types import Config
from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .generate import generate


logger = logging.getLogger(__name__)


class WatchHandler(FileSystemEventHandler):
    def __init__(self, conf: Config):
        self.conf = conf

        # Debounce update events to 1 second
        self._last_run = time.monotonic() - 1

    def on_any_event(self, event: FileSystemEvent) -> None:
        now = time.monotonic()
        if now - self._last_run >= 1:
            logger.info(f"Processing {event}")
            generate(conf=self.conf, tar=False)
            self._last_run = now
        else:
            logger.debug(f"Skipping event {event} (rate limited)")


def watch(*, conf: Config, path: str) -> int:
    event_handler = WatchHandler(conf)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
    return 0
