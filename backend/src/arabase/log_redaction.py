"""Keeps access tokens out of the server log.

The realtime socket authenticates with the access JWT in its query string
(``/ws/core/?jwt_token=…``, upstream's design, see ``realTimeHandler.js``), and
uvicorn logs every socket handshake and HTTP request with its full query
string. Each connection therefore wrote a live session token into the log at
INFO level — the CranL dashboard, and anything that ships those logs — where
anyone who can read the log could replay it until it expires.

``install`` puts a filter on the two uvicorn loggers that writes those lines
(``uvicorn.error`` for socket handshakes, ``uvicorn.access`` for requests) and
replaces the token value before a handler formats the record. A line without a
token is passed through after one substring check.
"""

import logging
import re

_TOKEN_PARAM = "jwt_token="
_TOKEN_VALUE = re.compile(r"(jwt_token=)[^&\s\"']+")
_REDACTED = r"\1[redacted]"

LOGGER_NAMES = ("uvicorn.error", "uvicorn.access")


def _redact(value):
    if isinstance(value, str) and _TOKEN_PARAM in value:
        return _TOKEN_VALUE.sub(_REDACTED, value)
    return value


class RedactTokenQueryFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(_redact(arg) for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = {key: _redact(arg) for key, arg in record.args.items()}
        return True


def install() -> None:
    for name in LOGGER_NAMES:
        logger = logging.getLogger(name)
        if not any(isinstance(f, RedactTokenQueryFilter) for f in logger.filters):
            logger.addFilter(RedactTokenQueryFilter())
