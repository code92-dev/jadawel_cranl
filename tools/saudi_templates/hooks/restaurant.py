"""The dishes became Saudi ones, so drop the photos that no longer match."""

KEEP = {"green omelette.jpeg", "caesar salad.jpeg", "cheese omelette.jpeg"}


def before(payload, lang):
    for app in payload["export"]:
        for table in app.get("tables", []):
            files = [f"field_{f['id']}" for f in table["fields"] if f["type"] == "file"]
            for row in table.get("rows", []):
                for key in files:
                    if row.get(key):
                        row[key] = [
                            f for f in row[key] if f.get("visible_name") in KEEP
                        ]
