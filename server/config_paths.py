"""Runtime path helpers for NetAlertX.

This module centralises path resolution so code can rely on the
Docker environment variables while still working during local
development and testing where those variables may not be set.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = [
    "APP_PATH",
    "DATA_PATH",
    "CONFIG_PATH",
    "DB_PATH",
    "TMP_PATH",
    "API_PATH",
    "LOG_PATH",
    "FRONT_PATH",
    "SERVER_PATH",
    "BACK_PATH",
    "PLUGINS_PATH",
    "REPORT_TEMPLATES_PATH",
    "API_PATH_WITH_TRAILING_SEP",
    "LOG_PATH_WITH_TRAILING_SEP",
    "CONFIG_PATH_WITH_TRAILING_SEP",
    "DB_PATH_WITH_TRAILING_SEP",
    "PLUGINS_PATH_WITH_TRAILING_SEP",
    "REPORT_TEMPLATES_PATH_WITH_TRAILING_SEP",
    "ensure_trailing_sep",
    "APP_PATH_STR",
    "DATA_PATH_STR",
    "CONFIG_PATH_STR",
    "DB_PATH_STR",
    "TMP_PATH_STR",
    "API_PATH_STR",
    "LOG_PATH_STR",
    "FRONT_PATH_STR",
    "SERVER_PATH_STR",
    "BACK_PATH_STR",
    "PLUGINS_PATH_STR",
    "REPORT_TEMPLATES_PATH_STR",
    "ensure_in_syspath",
]

_DEFAULT_APP_PATH = Path("/app")
_DEFAULT_DATA_PATH = Path("/data")
_DEFAULT_TMP_PATH = Path("/tmp")


def _resolve_env_path(variable: str, default: Path) -> Path:
    """Return the path from the environment or fall back to *default*."""
    value = os.getenv(variable)
    if value:
        return Path(value)
    return default


def ensure_trailing_sep(path: Path) -> str:
    """Return *path* as a string that always ends with the OS separator."""
    path_str = str(path)
    return path_str if path_str.endswith(os.sep) else f"{path_str}{os.sep}"


APP_PATH = _resolve_env_path("NETALERTX_APP", _DEFAULT_APP_PATH)
DATA_PATH = _resolve_env_path("NETALERTX_DATA", _DEFAULT_DATA_PATH)
CONFIG_PATH = _resolve_env_path("NETALERTX_CONFIG", DATA_PATH / "config")
DB_PATH = _resolve_env_path("NETALERTX_DB", DATA_PATH / "db")

TMP_PATH = _resolve_env_path("NETALERTX_TMP", _DEFAULT_TMP_PATH)
API_PATH = _resolve_env_path("NETALERTX_API", TMP_PATH / "api")
LOG_PATH = _resolve_env_path("NETALERTX_LOG", TMP_PATH / "log")

FRONT_PATH = APP_PATH / "front"
SERVER_PATH = APP_PATH / "server"
BACK_PATH = APP_PATH / "back"
PLUGINS_PATH = FRONT_PATH / "plugins"
REPORT_TEMPLATES_PATH = FRONT_PATH / "report_templates"

API_PATH_WITH_TRAILING_SEP = ensure_trailing_sep(API_PATH)
LOG_PATH_WITH_TRAILING_SEP = ensure_trailing_sep(LOG_PATH)
CONFIG_PATH_WITH_TRAILING_SEP = ensure_trailing_sep(CONFIG_PATH)
DB_PATH_WITH_TRAILING_SEP = ensure_trailing_sep(DB_PATH)
PLUGINS_PATH_WITH_TRAILING_SEP = ensure_trailing_sep(PLUGINS_PATH)
REPORT_TEMPLATES_PATH_WITH_TRAILING_SEP = ensure_trailing_sep(REPORT_TEMPLATES_PATH)

APP_PATH_STR = str(APP_PATH)
DATA_PATH_STR = str(DATA_PATH)
CONFIG_PATH_STR = str(CONFIG_PATH)
DB_PATH_STR = str(DB_PATH)
TMP_PATH_STR = str(TMP_PATH)
API_PATH_STR = str(API_PATH)
LOG_PATH_STR = str(LOG_PATH)
FRONT_PATH_STR = str(FRONT_PATH)
SERVER_PATH_STR = str(SERVER_PATH)
BACK_PATH_STR = str(BACK_PATH)
PLUGINS_PATH_STR = str(PLUGINS_PATH)
REPORT_TEMPLATES_PATH_STR = str(REPORT_TEMPLATES_PATH)


def ensure_in_syspath(path: Path) -> str:
    """Add *path* to ``sys.path`` if missing and return the string value."""
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)
    return path_str
