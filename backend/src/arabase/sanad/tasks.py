from jadawel.config.celery import app

SANAD_TURN_TIME_LIMIT = 300
"""Seconds. Well under ``handler.STALE_AFTER`` so a killed turn is reported
as failed only after its worker has certainly given up."""


@app.task(
    name="arabase.sanad.run_turn",
    queue="celery",
    soft_time_limit=SANAD_TURN_TIME_LIMIT,
    time_limit=SANAD_TURN_TIME_LIMIT + 30,
)
def run_sanad_turn(message_id: int, decisions: dict | None = None):
    from arabase.sanad.handler import SanadHandler

    SanadHandler().run(message_id, decisions)
