"""Add the VAT share of each expense and each supplier's VAT number."""

from common import add_field, find_table, formula_field, saudi_vat_number

NAMES = {
    "ar": (
        "المصروفات",
        "المبلغ شامل الضريبة",
        "ضريبة القيمة المضافة (15%)",
        "الموردون",
        "الرقم الضريبي",
        " ر.س",
        "",
    ),
    "en": (
        "Expenses",
        "Amount incl. VAT",
        "VAT (15%)",
        "Suppliers",
        "VAT number",
        "",
        "SAR ",
    ),
}


def patch(payload, lang):
    expenses, amount, vat, suppliers, vat_no, suffix, prefix = NAMES[lang]
    add_field(
        payload,
        find_table(payload, expenses),
        formula_field(
            vat,
            f"round(field('{amount}') * 15 / 115, 2)",
            suffix=suffix,
            prefix=prefix,
        ),
    )
    table = find_table(payload, suppliers)
    add_field(
        payload,
        table,
        {"type": "text", "name": vat_no, "text_default": ""},
        {row["id"]: saudi_vat_number(row["id"]) for row in table["rows"]},
    )
