"""Where a Sanad turn runs: a few threads in the web process, not Celery.

A turn is mostly waiting on the AI provider, often for a minute or more. The
small-plan deployment runs one Celery worker with a concurrency of 1
(``JADAWEL_RUN_MINIMAL``, see docs/DEPLOY_CRANL.md), and that worker also runs
automation workflows, publish jobs and realtime broadcasts. A turn queued there
held the only slot for its whole length, so the rows Sanad added could not
trigger their automations, nor could its own publish job run, until the turn
had ended. Threads add no process and no memory, and the work is I/O bound.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from django.db import connections

logger = logging.getLogger(__name__)

MAX_CONCURRENT_TURNS = 4
"""Per web process. Each chat runs one turn at a time (``SanadChatBusy``)."""

RUN_INLINE = False
"""Run turns in the calling thread; tests set this to assert on the outcome."""

_executor: Optional[ThreadPoolExecutor] = None
_executor_lock = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    # Created on first use, so it never exists before gunicorn forks.
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(
                max_workers=MAX_CONCURRENT_TURNS, thread_name_prefix="sanad-turn"
            )
        return _executor


def _run(message_id: int, decisions: Optional[dict]) -> None:
    from arabase.sanad.handler import SanadHandler

    try:
        SanadHandler().run(message_id, decisions)
    except Exception:  # noqa: BLE001 - nothing above this thread to report to
        logger.exception("Sanad turn %s crashed", message_id)
    finally:
        # Connections are per thread; close this one's so none are left open.
        connections.close_all()


def start_turn(message_id: int, decisions: Optional[dict] = None) -> None:
    """Run the model for ``message_id`` in the background.

    Call it only once the message is committed (``transaction.on_commit``).
    """

    if RUN_INLINE:
        from arabase.sanad.handler import SanadHandler

        SanadHandler().run(message_id, decisions)
        return
    _get_executor().submit(_run, message_id, decisions)
