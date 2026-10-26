"""
ParentConnect AI v2 -- Dialogflow ES fulfillment webhook.

The agent already answers everything from its built-in demo data, so this webhook is an UPGRADE, not a
requirement: switch it on (Fulfillment > Webhook) and the 53 webhook-enabled intents get live logic --
per-child context, ticket IDs, PIN-gated records, call transfer and voice (SSML) on every reply.

Run:      pip install flask gunicorn && gunicorn webhook:app
Env:      PC_REQUIRE_VERIFICATION=1   gate personal records behind the "verify me" PIN flow
          PC_DEMO_PIN=1234            the demo parent PIN
          PC_CONFIDENCE_GATE=0.7      below this, dynamic intents ask instead of guessing (deck slide 5)
"""
import os
import random
import re
import string

from flask import Flask, jsonify, request

import school_data as D

app = Flask(__name__)

REQUIRE_VERIFICATION = os.getenv("PC_REQUIRE_VERIFICATION", "0") == "1"
DEMO_PIN = os.getenv("PC_DEMO_PIN", "1234")
CONFIDENCE_GATE = float(os.getenv("PC_CONFIDENCE_GATE", "0.7"))

TRANSFER_NUMBERS = {   # E.164; replace with the school's real extensions before going live
    "office": "+914455550142", "principal": "+914455550150", "transport": "+914455550160",
    "fee office": "+914455550170", "admissions": "+914455550180", "default": "+914455550142"}

NAME_CHIPS = [f"{D.STUDENTS[k]['first']}'s attendance" for k in D.STUDENT_ORDER] + ["Main menu"]
CHIPS = {
    "student.select": ["Attendance", "Exam results", "Fees", "Homework", "Switch child", "Main menu"],
    "attendance.history": NAME_CHIPS,
    "attendance.absence": ["Message teacher", "Attendance", "Main menu"],
    "exams.schedule": ["Syllabus", "Study material", "Re-exam info", "Holidays", "Main menu"],
    "fees.due": ["Fee deadline", "Fee structure", "Fees", "Main menu"],
    "fees.receipt": ["Fees", "Talk to a person", "Main menu"],
    "info.transport": ["Contact school", "Timings", "Main menu"],
    "teachers.meeting": ["Teacher slots", "PTM", "Main menu"],
    "teachers.message": ["Meet a teacher", "Teacher slots", "Main menu"],
    "teachers.availability": ["Meet a teacher", "Message teacher", "Main menu"],
    "support.human": ["Contact school", "Main menu"],
    "support.complaint": ["Talk to a person", "Give feedback", "Main menu"],
    "support.feedback": ["Rate us", "Main menu"],
    "support.rating": ["Give feedback", "Main menu"],
    "support.feedback.capture": ["Rate us", "Main menu"],
    "support.complaint.details": ["Talk to a person", "Main menu"],
    "verify.parent": ["My children", "Main menu"],
    "input.unknown": ["Main menu", "Help", "Talk to a person"],
}

# ------------------------------------------------------------------ voice / SSML
_EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\uFE0F\u200D]+")


def voice_clean(text):
    text = _EMOJI.sub("", text)
    text = re.sub(r"\u20b9\s?([\d,]+)", r"\1 rupees", text)
    text = text.replace("\u2022", ",").replace("*", "").replace("#", "")
    return re.sub(r"\s+", " ", text).strip()


def to_ssml(text):
    clean = voice_clean(text).replace("&", "and").replace("<", "").replace(">", "")
    clean = re.sub(r'([.!?])\s+', r'\1 <break time="300ms"/> ', clean)
    return f"<speak>{clean}</speak>"


def voice_messages(spoken):
    ssml, plain = to_ssml(spoken), voice_clean(spoken)
    return [
        {"platform": "TELEPHONY", "telephonySynthesizeSpeech": {"ssml": ssml}},
        {"platform": "TELEPHONY", "text": {"text": [plain]}},
        {"platform": "ACTIONS_ON_GOOGLE",
         "simpleResponses": {"simpleResponses": [{"textToSpeech": ssml, "displayText": plain[:640]}]}},
    ]


# ------------------------------------------------------------------ request helpers
def norm(v):
    if isinstance(v, list):
        v = v[0] if v else ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return v if v != "" else None


def get_ctx(req, name):
    for c in req.get("queryResult", {}).get("outputContexts", []):
        if c.get("name", "").endswith(f"/contexts/{name}") and c.get("lifespanCount", 1) > 0:
            return c.get("parameters", {}) or {}
    return None


def active_student(req):
    for k in D.STUDENT_ORDER:
        if get_ctx(req, f"student-{k}") is not None:
            return D.STUDENTS[k]
    return None


def student_contexts(key):
    return [(f"student-{k}", 20 if k == key else 0, {}) for k in D.STUDENT_ORDER]


def ticket(prefix):
    return f"PC-{prefix}-" + "".join(random.choices(string.digits, k=4))


def reply(req, text, spoken=None, chips=(), contexts=(), transfer=None):
    session = req.get("session", "")
    msgs = [{"text": {"text": [text]}}]
    if chips:
        msgs.append({"quickReplies": {"title": "Choose an option", "quickReplies": list(chips)}})
        msgs.append({"payload": {"richContent": [[{"type": "chips", "options": [{"text": c} for c in chips]}]]}})
    msgs += voice_messages(spoken or text)
    if transfer:
        msgs.append({"platform": "TELEPHONY", "telephonyTransferCall": {"phoneNumber": transfer}})
    out = {"fulfillmentText": text, "fulfillmentMessages": msgs}
    if contexts:
        out["outputContexts"] = [{"name": f"{session}/contexts/{n}", "lifespanCount": life, "parameters": prm}
                                 for n, life, prm in contexts]
    return out


# ------------------------------------------------------------------ verification gate
def gate(req, s):
    """Return a reply if personal data for child `s` is locked, else None."""
    if not REQUIRE_VERIFICATION:
        return None
    ctx = get_ctx(req, "parent-verified")
    if ctx and ctx.get("student_id") == s["id"]:
        return None
    return reply(req, f"\U0001F510 {s['first']}'s records are protected.\n\nSay \"verify me\" and share the student ID "
                      f"and your 4-digit parent PIN.", "Please verify first. Say verify me, then share the student ID and PIN.",
                 ["Verify me", "Main menu"])


def gate_any(req):
    """Lock all-children views until at least one child is verified."""
    if not REQUIRE_VERIFICATION or get_ctx(req, "parent-verified") is not None:
        return None
    return reply(req, "\U0001F510 These records are protected.\n\nSay \"verify me\" and share the student ID and your 4-digit parent PIN.",
                 "Please verify first. Say verify me, then share the student ID and PIN.", ["Verify me", "Main menu"])


# ------------------------------------------------------------------ handlers
STUDENT_ACTION = re.compile(r"^student\.(select|attendance|results|fees|homework)\.([a-z]+)$")
CARDS = {"attendance": (D.attendance_card, D.attendance_spoken), "results": (D.results_card, D.results_spoken),
         "fees": (D.fees_card, D.fees_spoken), "homework": (D.homework_card, D.homework_spoken),
         "select": (D.dashboard_card, D.dashboard_spoken)}


def handle_student(req, feature, key):
    s = D.STUDENTS[key]
    locked = gate(req, s)
    if locked:
        return locked
    card, spoken = CARDS[feature]
    chips = CHIPS["student.select"] if feature == "select" else D.CARD_CHIPS[feature.capitalize()]
    return reply(req, card(s), spoken(s), chips, student_contexts(key))


def h_history(req, p):
    s = D.get_student(p.get("student_name"))
    locked = gate(req, s) if s else gate_any(req)
    if locked:
        return locked
    if not s:
        return reply(req, D.attendance_history_card(), "Here is the monthly attendance trend for all your children.",
                     CHIPS["attendance.history"])
    months = ["Jul", "Aug", "Sep", "Oct"]
    line = " \u2022 ".join(f"{m} {v}%" for m, v in zip(months, s["att_months"]))
    trend = s["att_months"][-1] - s["att_months"][0]
    note = "improving \U0001F4C8" if trend > 0 else "slipping \U0001F4C9" if trend < 0 else "steady"
    return reply(req, f"\U0001F4C5 Monthly attendance - {s['name']}\n\n{line}\n\nTrend since July: {note}",
                 f"{s['first']}'s attendance went from {s['att_months'][0]} percent in July to {s['att_months'][-1]} percent in October.",
                 CHIPS["attendance.history"], student_contexts(s["key"]))


def h_absence(req, p):
    s = D.get_student(p.get("student_name"))
    locked = gate(req, s) if s else None
    if locked:
        return locked
    who = s["first"] if s else (p.get("student_name") or "Your child")
    when = f" on {p['date']}" if p.get("date") else ""
    t = ticket("ABS")
    return reply(req, f"\U0001F4DD Absence noted ({t})\n\n{who} was absent{when} ({p.get('absence_reason')}). "
                      f"The class teacher has been notified.\n\nFor absences of more than 3 days, please send a medical certificate.",
                 f"Thanks, I've noted that {who} was absent because of {p.get('absence_reason')}. The class teacher has been informed.",
                 CHIPS["attendance.absence"], student_contexts(s["key"]) if s else ())


def h_exams(req, p):
    etype, subject = (p.get("exam_type") or "").lower(), p.get("subject")
    if etype in ("midterm",):
        t = "\U0001F5D3\ufe0f Midterm\n\nThe midterm ran 10-18 Sep and is completed \u2705. Results were published on 28 Sep - ask for a child's results."
        return reply(req, t, "The midterm is completed and results were published on 28 September.", CHIPS["exams.schedule"])
    if etype == "unit test":
        t = "\U0001F5D3\ufe0f Unit tests\n\nUnit tests are announced by each class teacher a week ahead and posted on the parent portal."
        return reply(req, t, "Unit tests are announced by the class teacher a week ahead.", CHIPS["exams.schedule"])
    if subject:
        for day, subj in D.EXAM_TIMETABLE:
            if subject.lower() in subj.lower():
                t = f"\U0001F5D3\ufe0f {subj} - final exam\n\n{day}, 9:00 AM (report by 8:15 AM)."
                return reply(req, t, f"The {subj} final exam is on {day}, at 9 AM.", CHIPS["exams.schedule"])
    return reply(req, D.exam_schedule_card(), D.exam_schedule_spoken(), CHIPS["exams.schedule"])


def h_fee_due(req, p):
    grade, ft, term = p.get("grade_class"), p.get("fee_type") or "Tuition", p.get("term")
    if term in D.TERM_DUE:
        line = f"{ft} fee for {grade} ({term}) is due on {D.TERM_DUE[term]}."
    else:
        line = D.fee_due_line(grade, ft)                       # deck slide 16, word for word
    nxt = f"Next due: {D.NEXT_TERM} - {D.TERM_DUE[D.NEXT_TERM]}. Grace period {D.GRACE_DAYS} days, then a late fee of {D.inr(D.LATE_FEE)}."
    return reply(req, f"\U0001F4B3 {line}\n\n{nxt}", f"{line} {nxt}", CHIPS["fees.due"])


def h_receipt(req, p):
    s = D.get_student(p.get("student_name")) or active_student(req)
    if not s:
        return reply(req, "\U0001F9FE Which child's receipt do you need?", "Which child's receipt do you need?",
                     [D.STUDENTS[k]["first"] for k in D.STUDENT_ORDER] + ["Main menu"])
    locked = gate(req, s)
    if locked:
        return locked
    if s["t1"]["status"] == "paid":
        rid = f"PC-R-{s['id'][3:]}-T1"
        t = (f"\U0001F9FE Receipt - {s['name']}\n\nTerm 1 paid on {s['t1']['on']} \u2022 Amount {D.inr(D.term_total(s))}\n"
             f"Receipt no. {rid} \u2022 emailed to the registered address.")
        sp = f"{s['first']}'s Term 1 payment of {D.inr_spoken(D.term_total(s))} was received on {s['t1']['on']}. Receipt {rid} has been emailed."
    else:
        t = (f"\U0001F9FE No receipt yet - {s['name']}\n\nNo Term 1 payment is recorded, so there is nothing to send. "
             f"Term 1 is overdue since {D.TERM_DUE['Term 1']}.")
        sp = f"There is no Term 1 payment recorded for {s['first']}, so no receipt exists yet."
    return reply(req, t, sp, CHIPS["fees.receipt"], student_contexts(s["key"]))


def h_transport(req, p):
    route = p.get("transport_route")
    return reply(req, D.transport_card(route), D.transport_spoken(route), CHIPS["info.transport"])


def h_availability(req, p):
    name = p.get("teacher_name")
    if name in D.TEACHERS:
        subj, slot = D.TEACHERS[name]
        return reply(req, f"\U0001F469\u200D\U0001F3EB {name} ({subj})\n\nAvailable: {slot}\nSay \"meet a teacher\" to request a slot.",
                     f"{name} teaches {subj} and is available {slot}.", CHIPS["teachers.availability"])
    return reply(req, D.teachers_card(), "Here are all the teachers' available slots.", CHIPS["teachers.availability"])


def h_meeting(req, p):
    name, t = p.get("teacher_name") or "the teacher", ticket("MTG")
    slot = f"\nTheir usual slot: {D.TEACHERS[name][1]}." if name in D.TEACHERS else ""
    when = f" for {p['date']}" if p.get("date") else ""
    return reply(req, f"\U0001F4C5 Meeting request sent ({t})\n\nI've asked {name}{when}.{slot}\nYou'll get an SMS confirmation within one working day.",
                 f"I've sent your meeting request to {name}. You'll get a confirmation within one working day.", CHIPS["teachers.meeting"])


def h_message(req, p):
    name, t = p.get("teacher_name") or "the teacher", ticket("MSG")
    return reply(req, f"\U0001F4AC Message queued ({t})\n\nYour message for {name} is queued. Teachers usually reply within one school day.",
                 f"Your message for {name} is queued. Teachers usually reply within one school day.", CHIPS["teachers.message"])


def h_human(req, p):
    kind = (p.get("contact_type") or "office")
    number = TRANSFER_NUMBERS.get(kind.lower(), TRANSFER_NUMBERS["default"])
    return reply(req, f"\U0001F64B Connecting you to the {kind}\n\nIf you're on a call, please hold while I transfer you. "
                      f"I've also flagged this chat so staff can follow up.",
                 f"Connecting you to the {kind}. Please hold while I transfer your call.", CHIPS["support.human"], transfer=number)


def h_complaint(req, p):
    cat, t = p.get("complaint_category"), ticket("CMP")
    return reply(req, f"\U0001F6E0\ufe0f Complaint registered ({t})\n\nCategory: {cat}\nA senior staff member reviews every complaint "
                      f"and the school replies within 2 working days.\n\nPlease type any details now and I'll attach them.",
                 f"I've registered your {cat} complaint, reference {' '.join(t[-4:])}. The school replies within 2 working days. Please tell me any details now.",
                 CHIPS["support.complaint"], [("awaiting-details", 2, {"ticket": t})])


def h_complaint_details(req, p):
    t = (get_ctx(req, "awaiting-details") or {}).get("ticket", "your complaint")
    return reply(req, f"\u2705 Details attached to {t}. The school will reply within 2 working days.",
                 "Thanks. I've attached those details to your complaint. The school will reply within 2 working days.",
                 CHIPS["support.complaint.details"])


def h_feedback(req, p):
    return reply(req, "\U0001F4A1 We'd love your feedback\n\nType your feedback in your next message and I'll pass it to the school.",
                 "We'd love your feedback. Please tell me what you'd like to share.", CHIPS["support.feedback"],
                 [("awaiting-feedback", 2, {})])


def h_feedback_capture(req, p):
    t = ticket("FDB")
    app.logger.info("feedback %s: %s", t, p.get("feedback_text"))
    return reply(req, f"\u2705 Thank you - feedback {t} recorded and passed to the school.",
                 "Thank you. I've recorded your feedback and passed it to the school.", CHIPS["support.feedback.capture"])


def h_rating(req, p):
    r = p.get("rating")
    try:
        r = max(1, min(5, int(r)))
    except (TypeError, ValueError):
        return reply(req, "Please give a rating from 1 to 5.", None, ["Give feedback", "Main menu"])
    msg = ("\u2b50" * r) + {5: " Wonderful - thank you!", 4: " Thank you! We'll keep improving.",
                            3: " Thanks - tell me what would make it better.",
                            2: " Sorry it fell short. Please tell me what went wrong.",
                            1: " I'm sorry. Please tell me what went wrong so we can fix it."}[r]
    return reply(req, f"{msg}\n\nYou rated us {r} out of 5.", f"Thank you for rating us {r} out of 5.", CHIPS["support.rating"])


def h_verify(req, p):
    sid, pin = p.get("student_id"), str(p.get("pin"))
    s = next((x for x in D.STUDENTS.values() if x["id"] == sid), None)
    if s and pin == DEMO_PIN:
        return reply(req, f"\u2705 Verified - {s['name']} ({s['id']}). Personal records are unlocked for this session.",
                     f"Thank you. You are verified for {s['first']}.", CHIPS["verify.parent"],
                     [("parent-verified", 50, {"student_id": s["id"]})])
    return reply(req, "\u274C I couldn't verify that student ID and PIN. Please try again.",
                 "I couldn't verify that student ID and PIN. Please try again.", ["Verify me", "Main menu"])


def h_unknown(req, p):
    app.logger.info("UNHANDLED: %s", req.get("queryResult", {}).get("queryText"))
    s = active_student(req)
    chips = (["Attendance", "Exam results", "Fees", "Homework"] if s else ["Main menu", "Help"]) + ["Talk to a person"]
    who = f" about {s['first']}" if s else ""
    return reply(req, f"Sorry, I didn't catch that. You can ask{who} about attendance, results, fees or homework, or say \"talk to a person\".",
                 "Sorry, I didn't catch that. You can ask about attendance, results, fees or homework, or say talk to a person.", chips)


ACTIONS = {
    "attendance.history": h_history, "attendance.absence": h_absence, "exams.schedule": h_exams,
    "fees.due": h_fee_due, "fees.receipt": h_receipt, "info.transport": h_transport,
    "teachers.availability": h_availability, "teachers.meeting": h_meeting, "teachers.message": h_message,
    "support.human": h_human, "support.complaint": h_complaint, "support.complaint.details": h_complaint_details,
    "support.feedback": h_feedback, "support.feedback.capture": h_feedback_capture, "support.rating": h_rating,
    "verify.parent": h_verify, "input.unknown": h_unknown,
}


@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(silent=True) or {}
    qr = req.get("queryResult", {})
    if not str(qr.get("languageCode", "en")).startswith("en"):
        return jsonify({})                       # Hindi/Tamil: let the agent's own translated replies through
    action = qr.get("action", "")
    p = {k: norm(v) for k, v in (qr.get("parameters") or {}).items()}

    m = STUDENT_ACTION.match(action)
    if m and m.group(2) in D.STUDENTS:
        return jsonify(handle_student(req, m.group(1), m.group(2)))

    conf = qr.get("intentDetectionConfidence")
    if action in ACTIONS and action != "input.unknown" and conf is not None and conf < CONFIDENCE_GATE:
        return jsonify(h_unknown(req, p))        # not sure enough to act: ask instead of guessing

    return jsonify(ACTIONS.get(action, h_unknown)(req, p))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "agent": "ParentConnect AI v2", "actions": len(ACTIONS) + 5,
                    "verification_required": REQUIRE_VERIFICATION})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
