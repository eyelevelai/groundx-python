import typing


def logging_config(name: str, level: str) -> typing.Dict[str, typing.Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - [%(process)d] - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "level": level.upper(),
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": "WARNING",
            },
            name: {
                "handlers": ["default"],
                "level": level.upper(),
                "propagate": False,
            },
            "gunicorn.error": {
                "level": "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
            "gunicorn.access": {
                "level": "WARNING",
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn": {"level": "INFO", "handlers": ["default"], "propagate": False},
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["default"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "WARNING",
                "handlers": ["default"],
                "propagate": False,
            },
        },
    }
