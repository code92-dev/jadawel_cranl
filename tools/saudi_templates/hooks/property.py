"""Saudi postal codes for the buildings, and no photos of US landmarks."""

POSTAL = {"Chicago": 12214, "New York": 23511, "Los Angeles": 32413}


def before(payload, lang):
    for app in payload["export"]:
        for table in app.get("tables", []):
            if table["name"] != "Buildings":
                continue
            ids = {f["name"]: f"field_{f['id']}" for f in table["fields"]}
            for row in table["rows"]:
                row[ids["Image"]] = []
                code = POSTAL.get(row.get(ids["City"]))
                if code:
                    row[ids["Zip code"]] = str(code + row["id"] % 7)

    # Ejar contract numbers are plain digits, not "CLA 1234".
    for app in payload["export"]:
        for table in app.get("tables", []):
            if table["name"] != "Leases":
                continue
            key = f"field_{next(f['id'] for f in table['fields'] if f['primary'])}"
            for row in table["rows"]:
                digits = str(row.get(key) or "").replace("CLA", "").strip()
                if digits.isdigit():
                    row[key] = f"20{digits}{digits[::-1]}"
