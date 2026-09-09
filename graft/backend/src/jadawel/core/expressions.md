# backend/src/jadawel/core/expressions.py

- Timezone · class · L4-L46 — class Timezone(Expression)
- __init__ · method · L18-L21 — def __init__(self, expression, timezone)
- resolve_expression · method · L23-L31 — def resolve_expression( self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False )
- __repr__ · method · L33-L38 — def __repr__(self)
- as_sql · method · L40-L46 — def as_sql(self, compiler, connection)
- DateTrunc · class · L49-L73 — class DateTrunc(Func)
- __init__ · method · L72-L73 — def __init__(self, trunc_type, field_expression, **extra)
- IsDistinctFrom · class · L77-L84 — class IsDistinctFrom(Lookup)
- as_sql · method · L80-L84 — def as_sql(self, compiler, connection)
