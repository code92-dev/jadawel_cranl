# backend/src/jadawel/config/db_routers.py

- set_db_alias · function · L11-L20 — def set_db_alias(alias: str) -> str
- get_db_alias · function · L23-L28 — def get_db_alias() -> str | None
- set_db_alias_for_read · function · L31-L56 — def set_db_alias_for_read()
- clear_db_state · function · L59-L63 — def clear_db_state()
- ReadReplicaRouter · class · L66-L89 — class ReadReplicaRouter
- db_for_read · method · L75-L76 — def db_for_read(self, model, **hints)
- db_for_write · method · L78-L79 — def db_for_write(self, model, **hints)
- allow_relation · method · L81-L86 — def allow_relation(self, obj1, obj2, **hints)
- allow_migrate · method · L88-L89 — def allow_migrate(self, db, app_label, model_name=None, **hints)
