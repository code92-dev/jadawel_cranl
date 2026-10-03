"""Saudi working calendar, Labor Law entitlements and a leave automation.

The upstream template has no automation, so this edition adds one with three
workflows: tell the approver about a new request, tell the employee about the
decision, and remind HR weekly while requests are still waiting.
"""

import datetime
import json
from pathlib import Path

from common import all_ids, find_table

TEMPLATES = Path(__file__).resolve().parents[3] / "backend" / "templates"

# Public holidays of the private sector in 2024 (the calendar's year): Founding
# Day, Eid al-Fitr (from the day after 29 Ramadan, four days), Eid al-Adha
# (from the Day of Arafah, four days) and National Day.
HOLIDAYS = {
    "2024-02-22",
    "2024-04-09",
    "2024-04-10",
    "2024-04-11",
    "2024-04-12",
    "2024-06-15",
    "2024-06-16",
    "2024-06-17",
    "2024-06-18",
    "2024-09-23",
}
WEEKEND = {4, 5}  # Friday and Saturday


def _ids(table):
    return {f["name"]: f"field_{f['id']}" for f in table["fields"]}


def before(payload, lang):
    calendar = find_table(payload, "OOO Calendar")
    ids = _ids(calendar)
    kind = next(f for f in calendar["fields"] if f["name"] == "Type")
    option = {o["value"]: o["id"] for o in kind["select_options"]}
    for row in calendar["rows"]:
        day = row[ids["Date"]]
        if day in HOLIDAYS:
            row[ids["Type"]] = option["Public Holiday"]
        elif datetime.date.fromisoformat(day).weekday() in WEEKEND:
            row[ids["Type"]] = option["Weekend"]
        else:
            row[ids["Type"]] = option["Weekday"]

    employees = find_table(payload, "Employees")
    days = _ids(employees)["Leave days / year"]
    for row in employees["rows"]:
        # 21 days, or 30 after five years of service (every fourth employee).
        row[days] = "30" if row["id"] % 4 == 0 else "21"


TEXT = {
    "ar": {
        "app": "أتمتة الإجازات",
        "local": "جداول المحلية",
        "smtp": "البريد (SMTP)",
        "from_name": "'الموارد البشرية'",
        "wf_new": "إشعار المعتمد بطلب جديد",
        "wf_decision": "إشعار الموظف بالقرار",
        "wf_weekly": "تذكير أسبوعي بالطلبات المعلّقة",
        "new_request": "طلب إجازة جديد",
        "get_employee": "جلب بيانات الموظف",
        "get_reviewer": "جلب بيانات المعتمد",
        "email_reviewer": "مراسلة المعتمد",
        "updated": "تحديث طلب إجازة",
        "check": "فحص القرار",
        "approved_edge": "معتمد",
        "rejected_edge": "مرفوض",
        "other_edge": "قيد المراجعة",
        "email_approved": "إبلاغ الموظف بالاعتماد",
        "email_rejected": "إبلاغ الموظف بالرفض",
        "weekly": "كل أحد الساعة 8 صباحًا",
        "pending": "الطلبات المعلّقة",
        "email_hr": "مراسلة الموارد البشرية",
        "approved": "معتمد",
        "rejected": "مرفوض",
        "subject_new": "concat('طلب إجازة جديد: ', {name})",
        "body_new": "concat('السلام عليكم،', '\n\n', 'قدّم ', {name}, ' طلب ', {reason}, ' من ', {start}, ' إلى ', {end}, '.', '\n', 'ملاحظات الطلب: ', {comments}, '\n\n', 'يُرجى مراجعة الطلب في جدول طلبات الإجازة.')",
        "subject_approved": "'اعتُمد طلب إجازتك'",
        "body_approved": "concat('مرحبًا ', {name}, '\n\n', 'اعتُمد طلب ', {reason}, ' من ', {start}, ' إلى ', {end}, '.', '\n', 'رصيدك المتبقي: ', {balance}, ' يومًا.', '\n', 'ملاحظات المعتمد: ', {review})",
        "subject_rejected": "'لم يُعتمد طلب إجازتك'",
        "body_rejected": "concat('مرحبًا ', {name}, '\n\n', 'نعتذر، لم يُعتمد طلب ', {reason}, ' من ', {start}, ' إلى ', {end}, '.', '\n', 'ملاحظات المعتمد: ', {review})",
        "subject_weekly": "'طلبات إجازة بانتظار الاعتماد'",
        "body_weekly": "'توجد طلبات إجازة لم تُعتمد بعد. راجعوها في عرض «الطلبات حسب الحالة» في جدول طلبات الإجازة.'",
        "check_pending": "هل توجد طلبات معلّقة؟",
        "has_pending": "توجد طلبات",
        "no_pending": "لا توجد طلبات",
    },
    "en": {
        "app": "Leave automation",
        "local": "Local Jadawel",
        "smtp": "SMTP Email",
        "from_name": "'Human Resources'",
        "wf_new": "Notify the approver of a new request",
        "wf_decision": "Notify the employee of the decision",
        "wf_weekly": "Weekly reminder of pending requests",
        "new_request": "New leave request",
        "get_employee": "Get the employee",
        "get_reviewer": "Get the approver",
        "email_reviewer": "Email the approver",
        "updated": "Leave request updated",
        "check": "Check the decision",
        "approved_edge": "Approved",
        "rejected_edge": "Rejected",
        "other_edge": "Under review",
        "email_approved": "Tell the employee it is approved",
        "email_rejected": "Tell the employee it is rejected",
        "weekly": "Every Sunday at 8 am",
        "pending": "Pending requests",
        "email_hr": "Email HR",
        "approved": "Approved",
        "rejected": "Rejected",
        "subject_new": "concat('New leave request: ', {name})",
        "body_new": "concat('Hello,', '\n\n', {name}, ' requested ', {reason}, ' from ', {start}, ' to ', {end}, '.', '\n', 'Comments: ', {comments}, '\n\n', 'Please review it in the leave requests table.')",
        "subject_approved": "'Your leave request is approved'",
        "body_approved": "concat('Hello ', {name}, '\n\n', 'Your ', {reason}, ' from ', {start}, ' to ', {end}, ' is approved.', '\n', 'Remaining balance: ', {balance}, ' days.', '\n', 'Approver comments: ', {review})",
        "subject_rejected": "'Your leave request was not approved'",
        "body_rejected": "concat('Hello ', {name}, '\n\n', 'Sorry, your ', {reason}, ' from ', {start}, ' to ', {end}, ' was not approved.', '\n', 'Approver comments: ', {review})",
        "subject_weekly": "'Leave requests waiting for approval'",
        "body_weekly": "'Some leave requests are still waiting for a decision. Review them in the requests-by-status view of the leave requests table.'",
        "check_pending": "Any pending requests?",
        "has_pending": "Pending requests",
        "no_pending": "No pending requests",
    },
}


def _formula(text, mode="simple"):
    return {"mode": mode, "version": "0.1", "formula": text}


def patch(payload, lang):
    t = TEXT[lang]
    requests = find_table(payload, "طلبات الإجازة" if lang == "ar" else "OOO Requests")
    employees = find_table(payload, "الموظفون" if lang == "ar" else "Employees")
    # Field names are translated by now; their ids come from the source export.
    rq = {name: f"field_{fid}" for name, fid in _source_ids(requests).items()}
    em = {name: f"field_{fid}" for name, fid in _source_ids(employees).items()}

    next_id = iter(range(max(all_ids(payload["export"])) + 1, 10**9))
    local = {
        "id": next(next_id),
        "name": t["local"],
        "order": "1.00000000000000000000",
        "type": "local_jadawel",
        "authorized_user": None,
    }
    smtp = {
        "id": next(next_id),
        "name": t["smtp"],
        "order": "2.00000000000000000000",
        "type": "smtp",
        "host": "smtp.example.sa",
        "port": 587,
        "use_tls": True,
        "username": None,
        "password": None,
    }

    def node(workflow, kind, label, **service):
        service_type = {"local_jadawel_update_row": "local_jadawel_upsert_row"}.get(
            kind, kind
        )
        integration = None
        if kind.startswith("local_jadawel"):
            integration = local["id"]
        elif kind == "smtp_email":
            integration = smtp["id"]
        n = {
            "id": next(next_id),
            "type": kind,
            "label": label,
            "service": {
                "id": next(next_id),
                "integration_id": integration,
                "type": service_type,
                "sample_data": None,
                **service,
            },
            "workflow_id": workflow["id"],
        }
        workflow["nodes"].append(n)
        return n

    def get_row(workflow, label, row_id):
        return node(
            workflow,
            "local_jadawel_get_row",
            label,
            table_id=employees["id"],
            view_id=None,
            search_query=_formula(""),
            filter_type="AND",
            filters=[],
            row_id=_formula(row_id),
        )

    def email(workflow, label, to, subject, body):
        return node(
            workflow,
            "smtp_email",
            label,
            from_email=_formula("'hr@example.sa'"),
            from_name=_formula(t["from_name"]),
            to_emails=_formula(to),
            cc_emails=_formula(""),
            bcc_emails=_formula(""),
            subject=_formula(subject, "advanced"),
            body_type="plain",
            body=_formula(body, "advanced"),
        )

    def workflow(name, order):
        return {
            "id": next(next_id),
            "name": name,
            "order": order,
            "state": "draft",
            "graph": {},
            "nodes": [],
        }

    def fields(trigger, employee=None, prefix="previous_node"):
        out = {
            "reason": f"get('{prefix}.{trigger}.0.{rq['Reason']}.0.value')",
            "start": f"get('{prefix}.{trigger}.0.{rq['From - input']}')",
            "end": f"get('{prefix}.{trigger}.0.{rq['Until - input']}')",
            "comments": f"get('{prefix}.{trigger}.0.{rq['Request comments']}')",
            "review": f"get('{prefix}.{trigger}.0.{rq['Review comments']}')",
        }
        if employee:
            out["name"] = f"get('previous_node.{employee}.{em['Name']}')"
            out["balance"] = (
                f"get('previous_node.{employee}.{em['Leave days balance']}')"
            )
        return out

    # 1. A new request reaches its approver.
    wf1 = workflow(t["wf_new"], 1)
    trigger = node(
        wf1, "local_jadawel_rows_created", t["new_request"], table_id=requests["id"]
    )
    employee = get_row(
        wf1,
        t["get_employee"],
        f"get('previous_node.{trigger['id']}.0.{rq['Employee']}.0.id')",
    )
    reviewer = get_row(
        wf1,
        t["get_reviewer"],
        f"get('previous_node.{employee['id']}.{em['OOO reviewer']}.0.id')",
    )
    v = fields(trigger["id"], employee["id"])
    mail = email(
        wf1,
        t["email_reviewer"],
        f"get('previous_node.{reviewer['id']}.{em['Email']}')",
        t["subject_new"].format(**v),
        t["body_new"].format(**v),
    )
    wf1["graph"] = {
        "0": trigger["id"],
        str(trigger["id"]): {"next": {"": [employee["id"]]}},
        str(employee["id"]): {"next": {"": [reviewer["id"]]}},
        str(reviewer["id"]): {"next": {"": [mail["id"]]}},
        str(mail["id"]): {},
    }

    # 2. The decision reaches the employee.
    wf2 = workflow(t["wf_decision"], 2)
    trigger = node(
        wf2, "local_jadawel_rows_updated", t["updated"], table_id=requests["id"]
    )
    employee = get_row(
        wf2,
        t["get_employee"],
        f"get('previous_node.{trigger['id']}.0.{rq['Employee']}.0.id')",
    )
    status = f"get('previous_node.{trigger['id']}.0.{rq['Status']}.value')"
    approved_uid, rejected_uid = (
        "5a1d0c2e-0b61-4d5e-9a57-6f0c1d2a7e11",
        "8c3e2f41-7d9a-4b0c-b2e6-1f4a9d5c3b22",
    )
    router = node(
        wf2,
        "router",
        t["check"],
        default_edge_label=t["other_edge"],
        edges=[
            {
                "label": t["approved_edge"],
                "uid": approved_uid,
                "condition": _formula(f"{status} = '{t['approved']}'", "advanced"),
            },
            {
                "label": t["rejected_edge"],
                "uid": rejected_uid,
                "condition": _formula(f"{status} = '{t['rejected']}'", "advanced"),
            },
        ],
    )
    v = fields(trigger["id"], employee["id"])
    to = f"get('previous_node.{employee['id']}.{em['Email']}')"
    ok = email(
        wf2,
        t["email_approved"],
        to,
        t["subject_approved"],
        t["body_approved"].format(**v),
    )
    no = email(
        wf2,
        t["email_rejected"],
        to,
        t["subject_rejected"],
        t["body_rejected"].format(**v),
    )
    wf2["graph"] = {
        "0": trigger["id"],
        str(trigger["id"]): {"next": {"": [employee["id"]]}},
        str(employee["id"]): {"next": {"": [router["id"]]}},
        str(router["id"]): {
            "next": {approved_uid: [ok["id"]], rejected_uid: [no["id"]]}
        },
        str(ok["id"]): {},
        str(no["id"]): {},
    }

    # 3. Every Sunday morning (05:00 UTC is 08:00 in Riyadh), HR gets the backlog.
    wf3 = workflow(t["wf_weekly"], 3)
    tick = node(
        wf3,
        "periodic",
        t["weekly"],
        interval="WEEK",
        minute=0,
        hour=5,
        day_of_week=6,
        day_of_month=1,
    )
    submitted = _submitted_option(requests, rq["Status"])
    pending = node(
        wf3,
        "local_jadawel_list_rows",
        t["pending"],
        table_id=requests["id"],
        view_id=None,
        sortings=[],
        search_query=_formula(""),
        filter_type="AND",
        filters=[
            {
                "field_id": int(rq["Status"][6:]),
                "type": "single_select_equal",
                "value": _formula(str(submitted)),
                "value_is_formula": False,
            }
        ],
        default_result_count=50,
    )
    # Upstream remaps list paths without a row index (`*.field_N` keeps its old
    # field id on import), so the digest checks for rows by id and points HR to
    # the view instead of listing names.
    none_uid = "3f6b1e0a-2c47-4d8e-a1b9-7e5d2c9f4a33"
    check = node(
        wf3,
        "router",
        t["check_pending"],
        default_edge_label=t["has_pending"],
        edges=[
            {
                "label": t["no_pending"],
                "uid": none_uid,
                "condition": _formula(
                    f"is_empty(get('previous_node.{pending['id']}.*.id'))", "advanced"
                ),
            }
        ],
    )
    hr = email(
        wf3, t["email_hr"], "'hr@example.sa'", t["subject_weekly"], t["body_weekly"]
    )
    wf3["graph"] = {
        "0": tick["id"],
        str(tick["id"]): {"next": {"": [pending["id"]]}},
        str(pending["id"]): {"next": {"": [check["id"]]}},
        str(check["id"]): {"next": {"": [hr["id"]]}},
        str(hr["id"]): {},
    }

    payload["export"].append(
        {
            "id": next(next_id),
            "name": t["app"],
            "order": len(payload["export"]) + 1,
            "type": "automation",
            "integrations": [local, smtp],
            "workflows": [wf1, wf2, wf3],
        }
    )


SOURCE_NAMES = {
    "Employee",
    "Reason",
    "Status",
    "From - input",
    "Until - input",
    "Request comments",
    "Review comments",
    "Employee (text)",
    "Name",
    "Email",
    "OOO reviewer",
    "Leave days balance",
}


def _source_ids(table):
    """Map the source (English) field names used above to their ids."""

    source = json.loads((TEMPLATES / "ooo-management.json").read_text())
    for app in source["export"]:
        for t in app.get("tables", []):
            if t["id"] == table["id"]:
                return {
                    f["name"]: f["id"] for f in t["fields"] if f["name"] in SOURCE_NAMES
                }
    raise KeyError(table["id"])


def _submitted_option(table, status_key):
    field = next(f for f in table["fields"] if f"field_{f['id']}" == status_key)
    # The first option of the source is "Submitted".
    return sorted(field["select_options"], key=lambda o: o["order"])[0]["id"]
