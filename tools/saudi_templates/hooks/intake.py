"""Email the sales team about urgent leads instead of posting to Slack."""

from common import clear_sample_data, find_table, slack_to_email

SUBJECT = {"ar": "'🔥 عميل محتمل عالي الأولوية'", "en": "'🔥 High-priority lead'"}


def before(payload, lang):
    submissions = find_table(payload, "Submissions")
    name = next(f["id"] for f in submissions["fields"] if f["name"] == "Full Name")
    for app in payload["export"]:
        if app["type"] != "automation":
            continue
        workflow = next(
            w for w in app["workflows"] if w["name"] == "New Lead Submission"
        )
        trigger = workflow["graph"]["0"]
        for node in workflow["nodes"]:
            if node["type"] != "slack_write_message":
                continue
            text = node["service"]["text"]["formula"]
            body = f"concat({text}, get('previous_node.{trigger}.0.field_{name}'))"
            node["service"]["text"]["formula"] = body
        slack_to_email(app, "'sales@example.sa'", SUBJECT[lang])


def patch(payload, lang):
    clear_sample_data(payload)
