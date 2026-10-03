"""Give students birth dates that fit their grade in the current school year."""

GRADES = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
SCHOOL_YEAR_START = 2026


def _table(payload, name):
    return next(
        t for a in payload["export"] for t in a.get("tables", []) if t["name"] == name
    )


def _field(table, name):
    return f"field_{next(f['id'] for f in table['fields'] if f['name'] == name)}"


def before(payload, lang):
    students = _table(payload, "Students")
    classes = _table(payload, "Classes")
    years = _table(payload, "Years")
    year_name = {r["id"]: r[_field(years, "Year")] for r in years["rows"]}
    class_grade = {}
    for row in classes["rows"]:
        linked = row.get(_field(classes, "Year")) or []
        if linked and year_name.get(linked[0]) in GRADES:
            class_grade[row["id"]] = GRADES.index(year_name[linked[0]])
    dob, klass = _field(students, "DOB"), _field(students, "Class")
    for row in students["rows"]:
        grade = next(
            (class_grade[c] for c in row.get(klass) or [] if c in class_grade), None
        )
        if grade is None or not row.get(dob):
            continue
        _, month, day = row[dob].split("-")
        # Six-year-olds start grade 1 in September; later birthdays wait a year.
        year = SCHOOL_YEAR_START - 6 - grade - (1 if month > "09" else 0)
        row[dob] = f"{year}-{month}-{day}"
