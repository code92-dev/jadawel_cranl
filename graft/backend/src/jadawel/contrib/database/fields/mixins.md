# backend/src/jadawel/contrib/database/fields/mixins.py

- get_date_time_format · function · L11-L18 — def get_date_time_format(options, format_type)
- BaseDateMixin · class · L21-L101 — class BaseDateMixin(models.Model)
- __init__ · method · L22-L26 — def __init__(self, *args, **kwargs) -> None: # Add retro-compatibility for the old timezone field.
- Meta · class · L52-L53 — class Meta
- get_python_format · method · L55-L64 — def get_python_format(self)
- get_psql_format · method · L66-L75 — def get_psql_format(self)
- get_psql_type · method · L77-L86 — def get_psql_type(self)
- get_psql_type_convert_function · method · L88-L98 — def get_psql_type_convert_function(self)
- _get_format · method · L100-L101 — def _get_format(self, format_type)
