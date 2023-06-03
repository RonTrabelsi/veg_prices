""" Loggers configuration """

from enum import Enum
from logging import config


class Loggers(Enum):
    DATA_COLLECTOR_LOGGER = "data_collector_logger"


LOGGERS_CONF = {
    "version": 1,
    "root": {
        "handlers": ["console"],
        "level": "INFO"
    },
    "loggers": {
        f"{Loggers.DATA_COLLECTOR_LOGGER.value}": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        }
    },
    "handlers": {
        "console": {
            "formatter": "std_out",
            "class": "logging.StreamHandler",
            "level": "DEBUG"
        },
    },
    "formatters": {
        "std_out": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(message)s",
            "datefmt": "%d-%m-%Y %I:%M:%S"
        }
    },
}


def load_loggers_conf() -> None:
    """ Load loggers configuration """
    config.dictConfig(LOGGERS_CONF)
