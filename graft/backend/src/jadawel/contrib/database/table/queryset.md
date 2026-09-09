# backend/src/jadawel/contrib/database/table/queryset.py

- CTEUpdateReturningIdsQueryCompiler · class · L8-L35 — class CTEUpdateReturningIdsQueryCompiler(SQLUpdateCompiler)
- as_sql · method · L15-L22 — def as_sql(self, *args, **kwargs)
- _as_sql · function · L16-L20 — def _as_sql()
- execute_sql · method · L24-L35 — def execute_sql(self, result_type)
- CTEUpdateRerurningQuery · class · L38-L39 — class CTEUpdateRerurningQuery(CTEUpdateQuery, CTEQuery)
- JadawelCTEQuery · class · L45-L60 — class JadawelCTEQuery(CTEQuery)
- __init__ · method · L50-L52 — def __init__(self, *args, **kwargs)
- chain · method · L54-L60 — def chain(self, klass=None)
- JadawelCTEQuerySet · class · L63-L79 — class JadawelCTEQuerySet(CTEQuerySet)
- __init__ · method · L69-L75 — def __init__(self, model=None, query=None, using=None, hints=None): # Only create an instance of a Query if this is the first invocation in # a query chain.
- update_returning_ids · method · L77-L79 — def update_returning_ids(self, **kwargs)
