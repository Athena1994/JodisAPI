from datetime import datetime
import logging
import os

from utils import path_builder
from app_config import LoggingConfig
import app_config

_formater = None
_log_path = None


# entries in config param overwrites default values from app config
def _configure_logger(name: str | None, config: dict) -> logging.Logger:
    log_cfg = app_config.get().logging

    logger = logging.getLogger(name)

    if config.get('use_file', log_cfg.use_file):
        log_file_name = config.get('file_name',
                                   f"{datetime.now().strftime('%m-%d-%Y')}.log")
        fileHandler = logging.FileHandler(
            os.path.join(_log_path, log_file_name))

        fileHandler.setFormatter(_formater)
        logger.addHandler(fileHandler)

    if config.get('use_stdout', log_cfg.use_stdout):
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(_formater)
        logger.addHandler(consoleHandler)

    logger.setLevel(config.get('verbosity', log_cfg.verbosity))

    return logger


def initialize(cfg: LoggingConfig) -> None:
    global _formater, _log_path

    _log_path = path_builder.build_path(cfg.log_path)

    print("initialize logging...")
    print(f"\t-use file: {cfg.use_file}")
    if cfg.use_file:
        print(f"\t-log path: {_log_path}")
    print(f"\t-use stdout: {cfg.use_stdout}")
    print(f"\t-verbosity: {cfg.verbosity}")

    if not os.path.exists(_log_path):
        os.makedirs(_log_path)

    _formater = logging.Formatter(cfg.format)
    _configure_logger(None, {})


def initialize_logger(name: str, config: dict = {}) -> logging.Logger:
    return _configure_logger(name, config)
