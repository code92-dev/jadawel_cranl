"""Send the critical alert by email instead of Slack, which needs a bot token."""

from common import clear_sample_data, find_table, slack_to_email

SUBJECT = {"ar": "'🚨 تنبيه سلامة حرج'", "en": "'🚨 Critical safety alert'"}
LABEL = {"ar": "تنبيه المفتش", "en": "Alert the inspector"}


def before(payload, lang):
    for app in payload["export"]:
        if app["type"] != "automation":
            continue
        workflow = app["workflows"][0]
        inspector = next(n for n in workflow["nodes"] if n["label"] == "Get inspector")
        table = find_table(payload, "Inspector")
        email = (
            f"field_{next(f['id'] for f in table['fields'] if f['name'] == 'Email')}"
        )
        for node in slack_to_email(
            app, f"get('previous_node.{inspector['id']}.{email}')", SUBJECT[lang]
        ):
            node["label"] = "Alert the inspector"


def patch(payload, lang):
    clear_sample_data(payload)
    for app in payload["export"]:
        for workflow in app.get("workflows", []):
            for node in workflow["nodes"]:
                if node["label"] == "Alert the inspector":
                    node["label"] = LABEL[lang]
