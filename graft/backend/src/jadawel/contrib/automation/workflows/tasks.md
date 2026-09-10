# backend/src/jadawel/contrib/automation/workflows/tasks.py

- start_workflow_celery_task · function · L23-L44 — def start_workflow_celery_task( workflow_id: int, history_id: int, )
- _start · function · L30-L36 — def _start()
- handle_workflow_dispatch_done · function · L50-L83 — def handle_workflow_dispatch_done( history_id: int, simulate_until_node_id: Optional[int] = None, )
- automation_periodic_cleanup · function · L90-L95 — def automation_periodic_cleanup()
- setup_periodic_automation_tasks · function · L99-L105 — def setup_periodic_automation_tasks(sender, **kwargs)
