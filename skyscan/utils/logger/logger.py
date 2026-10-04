"""Structured console logging system conforming to global rules.

Format: [PROCESS/DEF_NAME] function_name: LEVEL - message
Example: [IMG_PROCESS] process_image: INFO - Starting enhancement pipeline
"""
from __future__ import annotations

import inspect
import logging
import sys
import traceback
from typing import Any


class Formatter(logging.Formatter):
    """Custom formatter producing: [PROCESS/DEF_NAME] function_name: LEVEL - message"""

    def format(self, record: logging.LogRecord) -> str:
        proc_name = getattr(record, "proc_name", record.name)
        func_name = getattr(record, "caller_func", getattr(record, "funcName", "unknown"))
        level = record.levelname
        msg = record.getMessage()

        base = f"[{proc_name}] {func_name}: {level} - {msg}"
        if record.exc_info:
            exc_text = "".join(traceback.format_exception(*record.exc_info))
            base = f"{base}\n{exc_text}"
        elif record.exc_text:
            base = f"{base}\n{record.exc_text}"
        return base


def get_logger(proc_name: str) -> LogAdapter:
    """Get a structured logger adapter for a given process/component."""
    base_logger = logging.getLogger(f"skyscan.{proc_name}")
    if not base_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(Formatter())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.INFO)
        base_logger.propagate = False
    return LogAdapter(base_logger, proc_name)


class LogAdapter:
    """Adapter that injects process and caller function names into log records."""

    def __init__(self, logger: logging.Logger, proc_name: str) -> None:
        self.logger = logger
        self.proc_name = proc_name

    def _caller_func_name(self) -> str:
        try:
            stack = inspect.stack()
            if len(stack) > 2:
                return stack[2].function
        except Exception:
            pass
        return "unknown"

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        func = kwargs.pop("func_name", self._caller_func_name())
        extra = kwargs.setdefault("extra", {})
        extra["proc_name"] = self.proc_name
        extra["caller_func"] = func
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        func = kwargs.pop("func_name", self._caller_func_name())
        extra = kwargs.setdefault("extra", {})
        extra["proc_name"] = self.proc_name
        extra["caller_func"] = func
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        func = kwargs.pop("func_name", self._caller_func_name())
        extra = kwargs.setdefault("extra", {})
        extra["proc_name"] = self.proc_name
        extra["caller_func"] = func
        self.logger.warning(msg, *args, **kwargs)

    def warn(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        func = kwargs.pop("func_name", self._caller_func_name())
        extra = kwargs.setdefault("extra", {})
        extra["proc_name"] = self.proc_name
        extra["caller_func"] = func
        if "exc_info" not in kwargs and sys.exc_info()[0] is not None:
            kwargs["exc_info"] = True
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        func = kwargs.pop("func_name", self._caller_func_name())
        extra = kwargs.setdefault("extra", {})
        extra["proc_name"] = self.proc_name
        extra["caller_func"] = func
        if "exc_info" not in kwargs and sys.exc_info()[0] is not None:
            kwargs["exc_info"] = True
        self.logger.critical(msg, *args, **kwargs)
