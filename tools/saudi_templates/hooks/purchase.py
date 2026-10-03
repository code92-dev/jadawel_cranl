"""VAT on approved lines, and each supplier's VAT number and local content."""

from common import add_field, find_table, formula_field, saudi_vat_number

NAMES = {
    "ar": (
        "بنود الطلبات",
        "المجموع المعتمد",
        "ضريبة القيمة المضافة (15%)",
        "الإجمالي شامل الضريبة",
        "الموردون",
        "الرقم الضريبي",
        "نسبة المحتوى المحلي",
        " ر.س",
        "",
    ),
    "en": (
        "Request details",
        "Subtotal approved",
        "VAT (15%)",
        "Total incl. VAT",
        "Suppliers",
        "VAT number",
        "Local content",
        "",
        "SAR ",
    ),
}
LOCAL_CONTENT = [62, 45, 38, 71, 54]


def patch(payload, lang):
    (lines, subtotal, vat, total, suppliers, vat_no, local, suffix, prefix) = NAMES[
        lang
    ]
    table = find_table(payload, lines)
    add_field(
        payload,
        table,
        formula_field(
            vat, f"round(field('{subtotal}') * 0.15, 2)", suffix=suffix, prefix=prefix
        ),
    )
    add_field(
        payload,
        table,
        formula_field(
            total, f"round(field('{subtotal}') * 1.15, 2)", suffix=suffix, prefix=prefix
        ),
    )
    table = find_table(payload, suppliers)
    rows = sorted(table["rows"], key=lambda r: r["id"])
    add_field(
        payload,
        table,
        {"type": "text", "name": vat_no, "text_default": ""},
        {r["id"]: saudi_vat_number(r["id"]) for r in rows},
    )
    add_field(
        payload,
        table,
        {
            "type": "number",
            "name": local,
            "number_decimal_places": 0,
            "number_negative": False,
            "number_suffix": "%",
        },
        {
            r["id"]: str(LOCAL_CONTENT[i % len(LOCAL_CONTENT)])
            for i, r in enumerate(rows)
        },
    )
