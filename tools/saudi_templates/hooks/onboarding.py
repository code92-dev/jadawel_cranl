"""Arabic full names have no initials: drop the ". " after the father's name."""


def patch(payload, lang):
    for app in payload["export"]:
        for table in app.get("tables", []):
            for field in table["fields"]:
                if field.get("formula") and '". ", field(' in field["formula"]:
                    field["formula"] = field["formula"].replace(
                        '". ", field(', '" ", field('
                    )
