# backend/src/jadawel/core/telemetry/telemetry.py

- LogGuruCompatibleLoggerHandler · class · L14-L25 — class LogGuruCompatibleLoggerHandler(LoggingHandler)
- emit · method · L15-L25 — def emit(self, record: logging.LogRecord) -> None: # The Otel exporter does not handle nested dictionaries. Loguru stores all of # the extra log context developers can add on the extra dict. Here unnest # them as attributes on the record itself so otel can export them properly.
- setup_logging · function · L28-L62 — def setup_logging()
- setup_telemetry · function · L65-L111 — def setup_telemetry(add_django_instrumentation: bool)
- _setup_log_exporting · function · L114-L129 — def _setup_log_exporting(logger)
- _setup_celery_metrics · function · L140-L144 — def _setup_celery_metrics()
- count_task · function · L141-L142 — def count_task(sender, **kwargs)
- _setup_standard_backend_instrumentation · function · L147-L164 — def _setup_standard_backend_instrumentation()
- _setup_django_process_instrumentation · function · L167-L170 — def _setup_django_process_instrumentation()
