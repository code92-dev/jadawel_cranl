import logging

import pytest

from arabase.log_redaction import LOGGER_NAMES, RedactTokenQueryFilter, install

TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxfQ.c2lnbmF0dXJl"


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


@pytest.fixture
def capture():
    handler = _Capture()
    for name in LOGGER_NAMES:
        logging.getLogger(name).addHandler(handler)
    yield handler
    for name in LOGGER_NAMES:
        logging.getLogger(name).removeHandler(handler)


def test_installed_on_both_uvicorn_loggers_at_startup():
    for name in LOGGER_NAMES:
        filters = logging.getLogger(name).filters
        assert sum(isinstance(f, RedactTokenQueryFilter) for f in filters) == 1


def test_install_is_idempotent():
    install()
    install()

    for name in LOGGER_NAMES:
        filters = logging.getLogger(name).filters
        assert sum(isinstance(f, RedactTokenQueryFilter) for f in filters) == 1


def test_socket_handshake_line_loses_the_token(capture):
    # The exact call uvicorn's websocket protocols make on accept.
    logging.getLogger("uvicorn.error").info(
        '%s - "WebSocket %s" [accepted]',
        "188.48.85.197:0",
        f"/ws/core/?jwt_token={TOKEN}",
    )

    assert capture.lines == [
        '188.48.85.197:0 - "WebSocket /ws/core/?jwt_token=[redacted]" [accepted]'
    ]


def test_access_line_keeps_the_other_query_parameters(capture):
    # The exact call uvicorn's HTTP protocols make per request.
    logging.getLogger("uvicorn.access").info(
        '%s - "%s %s HTTP/%s" %d',
        "10.0.0.1:0",
        "GET",
        f"/ws/core/?jwt_token={TOKEN}&page=2",
        "1.1",
        101,
    )

    assert capture.lines == [
        '10.0.0.1:0 - "GET /ws/core/?jwt_token=[redacted]&page=2 HTTP/1.1" 101'
    ]


def test_lines_without_a_token_are_untouched(capture):
    logging.getLogger("uvicorn.access").info(
        '%s - "%s %s HTTP/%s" %d', "10.0.0.1:0", "GET", "/api/settings/", "1.1", 200
    )
    logging.getLogger("uvicorn.error").info("Application startup complete.")

    assert capture.lines == [
        '10.0.0.1:0 - "GET /api/settings/ HTTP/1.1" 200',
        "Application startup complete.",
    ]
