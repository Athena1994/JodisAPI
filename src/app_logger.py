
from dataclasses import dataclass
from datetime import datetime
import logging
import os

from utils import path_builder


@dataclass
class Config:
    verbosity: str
    log_path: str
    use_file: bool
    use_stdout: bool
    format: str

    DEFAULT_FMT = "%(asctime)s [%(threadName)-12.12s] " \
                  "[%(levelname)-5.5s]  %(message)s"

    @staticmethod
    def from_dict(d: dict) -> 'Config':
        return Config(
            verbosity=d.get('verbosity', 'DEBUG'),
            log_path=d.get('log_path', 'logs/'),
            use_file=d.get('use_file', False),
            use_stdout=d.get('use_stdout', True),
            format=d.get('format', Config.DEFAULT_FMT)
        )


def initialize(cfg: Config):
    log_path = path_builder.build_path(cfg.log_path)

    print("initialize logging...")
    print(f"\t-use file: {cfg.use_file}")
    if cfg.use_file:
        print(f"\t-log path: {log_path}")
    print(f"\t-use stdout: {cfg.use_stdout}")
    print(f"\t-verbosity: {cfg.verbosity}")

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    logFormatter = logging.Formatter(cfg.format)
    rootLogger = logging.getLogger()

    if cfg.use_file:
        log_file_name = f"{datetime.now().strftime('%m-%d-%Y')}.log"
        fileHandler = logging.FileHandler(os.path.join(log_path, log_file_name))
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

    if cfg.use_stdout:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    rootLogger.setLevel(cfg.verbosity)
