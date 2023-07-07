""" Loggers configuration """

from logging import config

PERIODIC_SCRAPER_LOGGER_NAME = "periodic_scraper_logger"

LOGGERS_CONF = {
    "version": 1,
    "root": {
        "handlers": ["console"],
        "level": "INFO"
    },
    "loggers": {
        PERIODIC_SCRAPER_LOGGER_NAME: {
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
