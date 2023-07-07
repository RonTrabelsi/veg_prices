""" Loggers configuration """

from enum import Enum
from logging import config


class Loggers(Enum):
    DATA_COLLECTOR_LOGGER = "data_collector_logger"
    PRICES_TRACKER_LOGGER = "prices_tracker_logger"


LOGGERS_CONF = {
    "version": 1,
    "root": {
        "handlers": ["console"],
        "level": "INFO"
    },
    "loggers": {
        Loggers.DATA_COLLECTOR_LOGGER.value: {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        },
        Loggers.PRICES_TRACKER_LOGGER.value: {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        },
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

# Load the loggers configuration when the module being imported
config.dictConfig(LOGGERS_CONF)
