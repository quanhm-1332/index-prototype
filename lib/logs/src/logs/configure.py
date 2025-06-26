from __future__ import annotations

import logging
import sys

import structlog
from structlog.stdlib import BoundLogger
from structlog.types import EventDict
from structlog.types import Processor


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


def setup_logging(
    log_level: str = "INFO",
):
    """set-up logging for the application

    Args:
        json_logs (bool, optional): True if logs should be in JSON format. Defaults to False.
        log_level (str, optional): The log level to use. Defaults to "INFO".
    """

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        drop_color_message_key,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            # Prepare event dict for `ProcessorFormatter`.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    log_renderer: structlog.types.Processor
    log_renderer = structlog.dev.ConsoleRenderer()
    formater_processors: list[Processor] = [
        structlog.stdlib.ProcessorFormatter.remove_processors_meta
    ]
    try:
        import logfire  # type: ignore[import]

        formater_processors.append(logfire.StructlogProcessor(console_log=True))
    except ImportError:
        pass
    formater_processors.append(log_renderer)
    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=formater_processors,
    )

    handler = logging.StreamHandler()
    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    for name in logging.root.manager.loggerDict:
        _l = logging.getLogger(name)
        _l.handlers.clear()
        _l.propagate = True

    def handle_exception(exc_type, exc_value, exc_traceback):
        """
        Log any uncaught exception instead of letting it be printed by Python
        (but leave KeyboardInterrupt untouched to allow users to Ctrl+C to stop)
        See https://stackoverflow.com/a/16993115/3641865
        """
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        root_logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

    sys.excepthook = handle_exception


def get_logger(name: str) -> BoundLogger:
    """Get a logger with the given name

    Args:
        name (str): The name of the logger

    Returns:
        BoundLogger: The logger
    """

    return structlog.stdlib.get_logger(name)
