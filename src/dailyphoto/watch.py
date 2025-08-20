import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent
from watchdog.events import FileSystemEventHandler

from dailyphoto.types import Config

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


class Watcher:
    def __init__(self, conf: Config, path: str):
        self.path = path
        self.event_handler = WatchHandler(conf)
        self.observer = Observer()
        self.thread = None

    def start(self) -> None:
        self.observer.schedule(self.event_handler, self.path, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        self.observer.stop()
        self.observer.join()


def watch(*, conf: Config, path: str) -> int:
    watcher = Watcher(conf, path)
    watcher.start()
    return 0
