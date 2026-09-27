"""Every number the ``formulas`` skill states, checked against the engine.

``backend/src/arabase/sanad/skills/formulas/SKILL.md`` teaches rounding modes,
precision, division by zero and date arithmetic for the two formula languages.
If an upstream upgrade changes any of them, this file fails before Sanad starts
teaching something false.
"""

from decimal import Decimal

import pytest

from jadawel.contrib.database.fields.handler import FieldHandler
from jadawel.contrib.database.rows.handler import RowHandler

# ---------------------------------------------------------------------------
# Table formula fields
# ---------------------------------------------------------------------------

# name -> (formula, expected value as text, expected decimal places or None)
TABLE_FACTS = {
    # Precision: +,-,* keep the most decimals of their inputs; / gives 10.
    "mul": ("field('Price') * field('Qty')", "22.50", 2),
    "div": ("field('Price') / field('Qty')", "2.5000000000", 10),
    "power_short": ("power(1.05, 12)", "1.80", 2),
    "power_long": ("power(1.050000, 12)", "1.795856", 6),
    # Rounding: half away from zero; negative places round to tens, hundreds…
    "round_half": ("round(2.5, 0)", "3", 0),
    "round_half_neg": ("round(-2.5, 0)", "-3", 0),
    "round_hundreds": ("round(1234.5, -2)", "1200", 0),
    "trunc": ("trunc(2.789)", "2", 0),
    "floor_neg": ("floor(-2.5)", "-3", 0),
    # Division by zero is NaN, not an error; error_to_null does not catch it.
    "div_zero": ("field('Price') / field('Zero')", "NaN", None),
    "div_zero_err_null": ("error_to_null(field('Price') / field('Zero'))", "NaN", None),
    "div_zero_when_nan": ("when_nan(field('Price') / field('Zero'), 0)", "0", None),
    "div_guard": (
        "if(field('Zero') = 0, 0, round(field('Price') / field('Zero'), 2))",
        "0",
        None,
    ),
    "tonumber_bad": ("tonumber('abc')", "NaN", None),
    # A blank number counts as 0 in arithmetic.
    "blank_plus": ("field('Price') + field('Blank')", "7.50", 2),
    "blank_times": ("field('Price') * field('Blank')", "0.00", 2),
    # Text keeps the field's decimals.
    "totext": ("totext(field('Price'))", "7.50", None),
    # Dates: 'mm'/'yy' count calendar boundaries crossed, not whole months.
    "mm_same_month": (
        "date_diff('mm', todate('20260101', 'YYYYMMDD'), "
        "todate('20260131', 'YYYYMMDD'))",
        "0",
        0,
    ),
    "mm_one_day": (
        "date_diff('mm', todate('20260131', 'YYYYMMDD'), "
        "todate('20260201', 'YYYYMMDD'))",
        "1",
        0,
    ),
    "yy_one_day": (
        "date_diff('yy', todate('20251231', 'YYYYMMDD'), "
        "todate('20260101', 'YYYYMMDD'))",
        "1",
        0,
    ),
    "dd": ("date_diff('dd', field('Start'), field('End'))", "43", 0),
    "month_end": ("field('Start') + date_interval('1 month')", "2026-02-28", None),
    "month_bucket": ("datetime_format(field('Start'), 'YYYY-MM')", "2026-01", None),
    "iso_week": ("datetime_format(field('Start'), 'IYYY-IW')", "2026-05", None),
    "quarter": (
        "concat(year(field('Start')), '-Q', ceil(month(field('Start')) / 3))",
        "2026-Q1",
        None,
    ),
    # Recipes the skill gives.
    "vat_line": ("round(field('Price') * field('Qty') * 0.15, 2)", "3.38", 2),
    "gross": ("round(field('Price') * field('Qty') * 1.15, 2)", "25.88", 2),
    "net_from_gross": ("round(25.88 / 1.15, 2)", "22.50", 2),
    "pct_change": (
        "if(field('Old') = 0, 0, round((field('New') - field('Old')) "
        "/ field('Old') * 100, 1))",
        "25.0",
        None,
    ),
    "age": (
        "year(field('End')) - year(field('Birth')) - if(datetime_format("
        "field('End'), 'MMDD') < datetime_format(field('Birth'), 'MMDD'), 1, 0)",
        "35",
        None,
    ),
    "pmt": (
        # 100,000 over 12 months at 6% a year (0.5% a month).
        "round(100000 * 0.005000 / (1 - power(1.005000, -12)), 2)",
        "8606.64",
        2,
    ),
    "overdue_days": (
        "if(field('Start') < today(), date_diff('dd', field('Start'), today()), 0)"
        " > 200",
        "True",
        None,
    ),
    "sum_lookup": ("sum(lookup('Items', 'Amount'))", "30.75", 2),
    "sum_filtered": (
        "sum(filter(lookup('Items', 'Amount'), lookup('Items', 'Amount') > 15))",
        "20.25",
        2,
    ),
    "join_lookup": ("join(totext(lookup('Items', 'Name')), ', ')", "pen, book", None),
    "count_links": ("count(field('Items'))", "2", 0),
    "select_text": ("totext(field('Tier'))", "Gold", None),
}


@pytest.mark.django_db
def test_table_formula_facts(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user, name="Facts")
    items = data_fixture.create_database_table(database=table.database, name="Items")
    handler = FieldHandler()
    item_name = data_fixture.create_text_field(table=items, name="Name", primary=True)
    amount = handler.create_field(
        user, items, "number", name="Amount", number_decimal_places=2
    )
    data_fixture.create_text_field(table=table, name="Title", primary=True)
    numbers = {
        name: handler.create_field(
            user, table, "number", name=name, number_decimal_places=places
        )
        for name, places in [
            ("Price", 2),
            ("Qty", 0),
            ("Zero", 0),
            ("Blank", 2),
            ("Old", 0),
            ("New", 0),
        ]
    }
    dates = {
        name: handler.create_field(user, table, "date", name=name)
        for name in ("Start", "End", "Birth")
    }
    tier = handler.create_field(
        user,
        table,
        "single_select",
        name="Tier",
        select_options=[{"value": "Gold", "color": "blue"}],
    )
    link = handler.create_field(
        user, table, "link_row", name="Items", link_row_table=items
    )
    rows = (
        RowHandler()
        .create_rows(
            user,
            items,
            [
                {f"field_{item_name.id}": "pen", f"field_{amount.id}": "10.50"},
                {f"field_{item_name.id}": "book", f"field_{amount.id}": "20.25"},
            ],
        )
        .created_rows
    )
    formulas = {
        name: handler.create_field(user, table, "formula", name=name, formula=formula)
        for name, (formula, _, _) in TABLE_FACTS.items()
    }
    RowHandler().create_rows(
        user,
        table,
        [
            {
                f"field_{numbers['Price'].id}": "7.50",
                f"field_{numbers['Qty'].id}": 3,
                f"field_{numbers['Zero'].id}": 0,
                f"field_{numbers['Old'].id}": 80,
                f"field_{numbers['New'].id}": 100,
                f"field_{dates['Start'].id}": "2026-01-31",
                f"field_{dates['End'].id}": "2026-03-15",
                f"field_{dates['Birth'].id}": "1990-06-01",
                f"field_{tier.id}": tier.select_options.first().id,
                f"field_{link.id}": [row.id for row in rows],
            }
        ],
    )
    row = table.get_model().objects.get()

    wrong = {}
    for name, (formula, expected, places) in TABLE_FACTS.items():
        field = formulas[name].specific
        value = getattr(row, f"field_{field.id}")
        text = "NaN" if isinstance(value, Decimal) and value.is_nan() else str(value)
        if expected != "NaN" and isinstance(value, Decimal):
            text = str(value) if places is not None else str(value.normalize())
            if places is None:
                expected = str(Decimal(expected).normalize())
        if text != expected or (
            places is not None and field.number_decimal_places != places
        ):
            wrong[name] = (text, field.number_decimal_places, field.error)
    assert wrong == {}


# ---------------------------------------------------------------------------
# Runtime formulas (automation steps and app pages)
# ---------------------------------------------------------------------------


class Context(dict):
    """The little a runtime formula needs: a few values and a timezone."""

    values = {
        "n": 7,
        "zero": 0,
        "list": [1, 2, 3.5],
        "rows": [{"amount": 10.5}, {"amount": 20.25}],
        "day": "2026-02-03",
    }

    def __getitem__(self, key):
        parts = key.split(".")
        if parts[:2] == ["rows", "*"]:
            return [row[parts[2]] for row in self.values["rows"]]
        return self.values[parts[0]]

    def get_timezone_name(self):
        return "Asia/Riyadh"


RUNTIME_FACTS = {
    # Operators work as well as functions.
    "get('n') * 2 + 1": 15,
    "get('n') / 2": 3.5,
    # round defaults to 2 places and rounds half to even (banker's rounding).
    "round(2.555)": 2.56,
    "round(2.5, 0)": 2.0,
    "round(3.5, 0)": 4.0,
    "round(-2.5, 0)": -2.0,
    # Binary floating point: 1.005 is stored just below 1.005.
    "round(1.005, 2)": 1.0,
    "0.1 + 0.2": 0.30000000000000004,
    # number_format: 0 decimals unless told; separators ',', '.', ' ', ''.
    "number_format(1234.5)": "1,234",
    "number_format(1234567.891, 2)": "1,234,567.89",
    "number_format(1234.5, 2, ' ', ',')": "1 234,50",
    "number_format(0.1 + 0.2, 2)": "0.30",
    # concat turns 2.50 into '2.5'.
    "concat('SAR ', 2.50)": "SAR 2.5",
    "sum(get('rows.*.amount'))": 30.75,
    "equal(get('n'), '7')": False,
    "get('n') = 7": True,
    "'7' + 3": 10,
    # if() evaluates both branches, so the divisor itself must never be zero.
    "if(get('zero') = 0, 0, get('n') / if(get('zero') = 0, 1, get('zero')))": 0,
    "datetime_format(get('day'), 'DD/MM/YYYY')": "03/02/2026",
    "datetime_format(get('day'), 'YYYY-MM')": "2026-02",
}


@pytest.mark.parametrize("formula,expected", RUNTIME_FACTS.items())
def test_runtime_formula_facts(formula, expected):
    from jadawel.core.formula import JadawelFormulaObject, resolve_formula
    from jadawel.core.formula.registries import formula_runtime_function_registry

    value = resolve_formula(
        JadawelFormulaObject.create(formula),
        formula_runtime_function_registry,
        Context(),
    )
    assert value == expected


@pytest.mark.parametrize(
    "formula",
    [
        "get('n') / get('zero')",
        # Not a guard: if() still evaluates the division it would skip.
        "if(get('zero') = 0, 0, get('n') / get('zero'))",
    ],
)
def test_runtime_division_by_zero_is_an_error(formula):
    from jadawel.core.formula import JadawelFormulaObject, resolve_formula
    from jadawel.core.formula.registries import formula_runtime_function_registry

    with pytest.raises(ZeroDivisionError):
        resolve_formula(
            JadawelFormulaObject.create(formula),
            formula_runtime_function_registry,
            Context(),
        )
