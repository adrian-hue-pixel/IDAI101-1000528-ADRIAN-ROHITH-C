"""
ParentConnect AI v2 -- shared school data + response text.

Used by BOTH:
  * build_agent.py  -> static responses baked into the Dialogflow agent
                       (so the bot works the moment the zip is imported)
  * webhook.py      -> live responses when the webhook is switched on
Because both import the same functions, console demo and webhook can
never disagree. Swap the dicts for real SIS / fee / exam API calls later.
"""

import math

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def inr(n):
    return f"\u20b9{n:,.0f}"


def inr_spoken(n):
    return f"{n:,.0f} rupees"


def grade_number(grade):
    digits = "".join(c for c in str(grade) if c.isdigit())
    return int(digits) if digits else 0


def grade_letter(pct):
    if pct >= 90:
        return "A+"
    if pct >= 80:
        return "A"
    if pct >= 70:
        return "B+"
    if pct >= 60:
        return "B"
    return "C"


# ---------------------------------------------------------------------------
# Fees (per term, by grade band) -- matches the deck's "Grade 5 tuition due 15 Aug"
# ---------------------------------------------------------------------------
TERM_DUE = {"Term 1": "15 Aug", "Term 2": "15 Nov", "Term 3": "15 Feb"}
NEXT_TERM = "Term 2"
LATE_FEE = 200
GRACE_DAYS = 7
ACTIVITIES_FEE = 1500
EXAM_FEE = 750
ROUTE_FEE = {"Route 4": 4500, "Route 7": 4800, "Route 12": 5200}


def tuition_for(grade):
    g = grade_number(grade)
    if g <= 5:
        return 18000
    if g <= 8:
        return 22000
    if g <= 10:
        return 26000
    return 30000


FEE_BANDS = [("Grade 1-5", 18000), ("Grade 6-8", 22000),
             ("Grade 9-10", 26000), ("Grade 11-12", 30000)]

# ---------------------------------------------------------------------------
# Students (demo records)
# ---------------------------------------------------------------------------
STUDENTS = {
    "aarav": {
        "key": "aarav", "first": "Aarav", "name": "Aarav Sharma", "id": "ADM41872",
        "grade": "Grade 8", "section": "B", "route": "Route 4",
        "att_present": 92, "att_total": 100, "att_months": [94, 90, 91, 93],
        "marks": {"Mathematics": 87, "Science": 91, "English": 84, "Social Studies": 82, "Hindi": 88},
        "rank": 4, "class_size": 38,
        "remark": "Excellent in Science. Practising longer written answers in English will push the score higher.",
        "t1": {"status": "paid", "on": "12 May"},
        "homework": [("Mathematics", "Exercise 4.2, Q1-10"),
                     ("Science", "Read Chapter 6 and answer the review questions"),
                     ("English", "Write a 150-word diary entry")],
    },
    "diya": {
        "key": "diya", "first": "Diya", "name": "Diya Menon", "id": "ADM52390",
        "grade": "Grade 5", "section": "A", "route": None,
        "att_present": 88, "att_total": 100, "att_months": [90, 86, 88, 88],
        "marks": {"Mathematics": 79, "Science": 84, "English": 90, "Social Studies": 81, "Hindi": 86},
        "rank": 9, "class_size": 34,
        "remark": "English is a clear strength. A little extra practice with multiplication tables will help Mathematics.",
        "t1": {"status": "paid", "on": "10 May"},
        "homework": [("English", "Write a paragraph on 'My Favourite Season'"),
                     ("Mathematics", "Multiplication worksheet 3"),
                     ("EVS", "Plant diary: observe and draw your seedling")],
    },
    "kabir": {
        "key": "kabir", "first": "Kabir", "name": "Kabir Nair", "id": "ADM48215",
        "grade": "Grade 6", "section": "C", "route": "Route 7",
        "att_present": 71, "att_total": 100, "att_months": [74, 69, 70, 71],
        "marks": {"Mathematics": 68, "Science": 72, "English": 70, "Social Studies": 66, "Hindi": 74},
        "rank": 21, "class_size": 36,
        "remark": "Steady improvement. Regular attendance will lift every subject.",
        "t1": {"status": "overdue", "on": None},
        "homework": [("Science", "Chapter 2 questions 1-8"),
                     ("Mathematics", "Fractions worksheet"),
                     ("Social Studies", "Mark five rivers on the outline map")],
    },
    "ishita": {
        "key": "ishita", "first": "Ishita", "name": "Ishita Rao", "id": "ADM63107",
        "grade": "Grade 8", "section": "B", "route": None,
        "att_present": 95, "att_total": 100, "att_months": [96, 94, 95, 95],
        "marks": {"Mathematics": 93, "Science": 89, "English": 92, "Social Studies": 90, "Hindi": 94},
        "rank": 1, "class_size": 38,
        "remark": "Outstanding all-rounder. Consider the Science Olympiad this term.",
        "t1": {"status": "paid", "on": "02 Aug"},
        "homework": [("Mathematics", "Exercise 4.2, Q1-10"),
                     ("Science", "Read Chapter 6 and answer the review questions"),
                     ("English", "Write a 150-word diary entry")],
    },
}
STUDENT_ORDER = ["aarav", "diya", "kabir", "ishita"]


def get_student(key_or_name):
    if not key_or_name:
        return None
    k = str(key_or_name).strip().lower().split()[0]
    return STUDENTS.get(k)


def att_pct(s):
    return round(100 * s["att_present"] / s["att_total"])


def att_days_needed(s, target=75):
    p, t = s["att_present"], s["att_total"]
    if 100 * p / t >= target:
        return 0
    return math.ceil((target / 100 * t - p) / (1 - target / 100))


def avg_pct(s):
    m = s["marks"]
    return round(sum(m.values()) / len(m), 1)


def pct_str(x):
    return f"{x:g}"


def class_label(s):
    return f"{s['grade']}-{s['section']}"


def term_total(s):
    t = tuition_for(s["grade"]) + ACTIVITIES_FEE + EXAM_FEE
    if s["route"]:
        t += ROUTE_FEE[s["route"]]
    return t


# ---------------------------------------------------------------------------
# Per-student cards (chat text) and spoken lines (voice)
# ---------------------------------------------------------------------------

def attendance_card(s):
    pct = att_pct(s)
    need = att_days_needed(s)
    if pct >= 90:
        status = "Excellent \u2705"
    elif need == 0:
        status = "Good standing \u2705"
    else:
        status = f"\u26a0\ufe0f Below the 75% minimum. {s['first']} needs {need} more days present in a row to reach 75%."
    return (f"\U0001F4D8 Attendance - {s['name']}\n{class_label(s)} \u2022 ID {s['id']}\n\n"
            f"Present: {s['att_present']} of {s['att_total']} school days ({pct}%)\n"
            f"Absent: {s['att_total'] - s['att_present']} days\n"
            f"Status: {status}\n\nMinimum required by the school: 75%.")


def attendance_spoken(s):
    pct = att_pct(s)
    line = f"{s['first']}'s attendance is {pct}% this term."
    if att_days_needed(s):
        line += f" That is below the 75% minimum, so {s['first']} needs {att_days_needed(s)} more days present in a row."
    return line


def _strength_focus(s):
    best = max(s["marks"], key=s["marks"].get)
    low = min(s["marks"], key=s["marks"].get)
    return best, low


def results_card(s):
    avg = avg_pct(s)
    best, low = _strength_focus(s)
    marks = " \u2022 ".join(f"{k} {v}" for k, v in s["marks"].items())
    return (f"\U0001F4CA Midterm Result - {s['name']}\n{class_label(s)} \u2022 Published 28 Sep\n\n"
            f"{marks}\n(each out of 100)\n\n"
            f"Overall: {pct_str(avg)}% \u2022 Grade {grade_letter(avg)} \u2022 Class rank {s['rank']} of {s['class_size']}\n"
            f"\u2b50 Strength: {best} ({s['marks'][best]})\n"
            f"\U0001F4C8 Focus area: {low} ({s['marks'][low]})\n\n"
            f"Teacher's note: {s['remark']}")


def results_spoken(s):
    best, _ = _strength_focus(s)
    return (f"{s['first']} scored {pct_str(avg_pct(s))} percent overall in the midterm, grade {grade_letter(avg_pct(s))}, "
            f"with a class rank of {s['rank']} out of {s['class_size']}. {best} is the strongest subject.")


def fees_card(s):
    tut = tuition_for(s["grade"])
    total = term_total(s)
    parts = [f"Tuition {inr(tut)}", f"Activities {inr(ACTIVITIES_FEE)}", f"Exam {inr(EXAM_FEE)}"]
    if s["route"]:
        parts.append(f"Transport ({s['route']}) {inr(ROUTE_FEE[s['route']])}")
    t1 = s["t1"]
    if t1["status"] == "paid":
        t1_line = f"Term 1: {inr(total)} - Paid \u2705 on {t1['on']}"
        alert = ""
    else:
        t1_line = f"Term 1: {inr(total)} - \u26a0\ufe0f OVERDUE since {TERM_DUE['Term 1']}"
        alert = (f"\n\nA late fee of {inr(LATE_FEE)} applies after the {GRACE_DAYS}-day grace period. "
                 "Please pay at the fee office or the parent portal.")
    sep = " \u2022 "
    breakdown = sep.join(parts)
    return (f"\U0001F4B3 Fee Status - {s['name']}\n{class_label(s)} \u2022 ID {s['id']}\n\n"
            f"{t1_line}\n"
            f"{NEXT_TERM}: {inr(total)} - due {TERM_DUE[NEXT_TERM]}\n"
            f"Term 3: {inr(total)} - due {TERM_DUE['Term 3']}\n\n"
            f"Per-term breakdown: {breakdown}{alert}")


def fees_spoken(s):
    total = term_total(s)
    if s["t1"]["status"] == "paid":
        return (f"{s['first']}'s Term 1 fee is paid. The Term 2 fee of {inr_spoken(total)} "
                f"is due on {TERM_DUE[NEXT_TERM].replace('Nov', 'November')}.")
    return (f"{s['first']}'s Term 1 fee of {inr_spoken(total)} is overdue since 15 August. "
            f"A late fee of {inr_spoken(LATE_FEE)} applies.")


def homework_card(s):
    lines = "\n".join(f"\u2022 {subj} - {task}" for subj, task in s["homework"])
    return (f"\U0001F4DA Homework - {s['first']} ({class_label(s)})\n\n{lines}\n\n"
            f"Due tomorrow unless the teacher says otherwise. {len(s['homework'])} subjects today.")


def homework_spoken(s):
    items = ", ".join(f"{subj}: {task}" for subj, task in s["homework"])
    return f"Homework for {s['first']} today. {items}."


def dashboard_card(s):
    pct = att_pct(s)
    flag = "\u26a0\ufe0f" if att_days_needed(s) else "\u2705"
    fee = ("Term 1 paid \u2705" if s["t1"]["status"] == "paid" else "Term 1 OVERDUE \u26a0\ufe0f")
    return (f"\U0001F9D2 {s['name']} \u2022 {class_label(s)} \u2022 ID {s['id']}\n\n"
            f"\U0001F4D8 Attendance: {pct}% {flag}\n"
            f"\U0001F4CA Midterm: {pct_str(avg_pct(s))}% (Grade {grade_letter(avg_pct(s))}) \u2022 Rank {s['rank']}/{s['class_size']}\n"
            f"\U0001F4B3 Fees: {fee} \u2022 next due {TERM_DUE[NEXT_TERM]}\n\n"
            f"{s['first']} is now your active child. Ask me about attendance, results, fees or homework.")


def dashboard_spoken(s):
    return (f"Showing {s['first']}. Attendance is {att_pct(s)} percent, the midterm average is {pct_str(avg_pct(s))} percent, "
            f"and the next fee is due on {TERM_DUE[NEXT_TERM].replace('Nov', 'November')}. "
            f"What would you like to check?")


# ---------------------------------------------------------------------------
# School-wide data and cards (placeholders in $param form are passed in by the
# agent builder so the console can echo what the parent asked about)
# ---------------------------------------------------------------------------
EXAM_TIMETABLE = [("Wed 2 Dec", "English"), ("Fri 4 Dec", "Science"), ("Mon 7 Dec", "Mathematics"),
                  ("Wed 9 Dec", "Social Studies"), ("Thu 10 Dec", "Hindi / Second Language"),
                  ("Fri 11 Dec", "Computer Science")]

HOLIDAYS = [("Deepavali break", "7-9 Nov 2026"), ("Christmas", "Fri 25 Dec 2026"),
            ("Pongal break", "14-17 Jan 2027"), ("Republic Day", "Tue 26 Jan 2027")]

EVENTS = [("Science Exhibition", "Thu 12 Nov", "Academic"), ("Children's Day Celebration", "Sat 14 Nov", "Cultural"),
          ("Parent-Teacher Meeting", "Sat 28 Nov", "PTM"), ("Annual Day", "Fri 18 Dec", "Cultural")]

ANNOUNCEMENTS = {
    "Urgent": ("Route 7 running late", "The Route 7 bus is running about 20 minutes late this week because of road work. "
               "Students stay supervised on campus until boarding."),
    "Event": ("Science Exhibition", "The Science Exhibition is on Thu 12 Nov. Project registration closes Thu 5 Nov."),
    "Academic": ("Final exam timetable released", "Final exams run 2-11 Dec. Unit-wise syllabus PDFs are on the parent portal."),
    "General": ("Winter uniform from 1 Nov", "The navy sweater becomes part of the uniform from 1 Nov."),
}

ROUTES = {
    "Route 4": ("North", "7:15 AM", "3:00 PM"),
    "Route 7": ("Central", "7:30 AM", "3:15 PM"),
    "Route 12": ("South", "7:40 AM", "3:25 PM"),
}

CONTACTS = {
    "Office": "(044) 555-0142", "Principal": "(044) 555-0150", "Transport": "(044) 555-0160",
    "Fee office": "(044) 555-0170", "Admissions": "(044) 555-0180",
}

TEACHERS = {
    "Mrs. Sharma": ("Mathematics", "Mon-Thu, 3:00-3:45 PM"),
    "Mr. Rao": ("Science", "Tue & Thu, 2:30-3:15 PM"),
    "Ms. Verma": ("English", "Mon, Wed & Fri, 2:45-3:30 PM"),
    "Mr. Iyer": ("Hindi / Social Studies", "Tue-Fri, 3:00-3:30 PM"),
}


def exam_schedule_card():
    rows = "\n".join(f"\u2022 {d} - {s}" for d, s in EXAM_TIMETABLE)
    return ("\U0001F5D3\ufe0f Exam Schedule\n\nMidterm (10-18 Sep): completed \u2705 - results published 28 Sep\n"
            f"Final exams: 2-11 Dec 2026\n\n{rows}\n\nReport by 8:15 AM \u2022 Papers start 9:00 AM\n"
            "Bring: school ID, two pens, pencil and geometry box.")


def exam_schedule_spoken():
    return ("The final exams run from 2 to 11 December, starting with English on 2 December. "
            "Please report by 8:15 in the morning.")


def holidays_card():
    rows = "\n".join(f"\u2022 {n} - {d}" for n, d in HOLIDAYS)
    return f"\U0001F334 Upcoming Holidays\n\n{rows}\n\nDates follow the school calendar; circulars confirm any change."


def holidays_spoken():
    n, d = HOLIDAYS[0]
    return f"The next holiday is the {n}, on {d}."


def events_card():
    rows = "\n".join(f"\u2022 {d} - {n} ({t})" for n, d, t in EVENTS)
    return f"\U0001F389 Upcoming Events\n\n{rows}\n\nAsk me for the PTM details or announcements any time."


def events_spoken():
    n, d, _ = EVENTS[0]
    return f"The next event is the {n} on {d}."


def ptm_card():
    return ("\U0001F468\u200D\U0001F469\u200D\U0001F467 Parent-Teacher Meeting\n\nDate: Saturday 28 Nov 2026\n"
            "Time: 10:00 AM - 1:00 PM (all grades)\nVenue: your child's classroom\n\n"
            "Each parent gets a 10-minute slot. Say 'meet a teacher' and I will request one for you.")


def ptm_spoken():
    return "The parent teacher meeting is on Saturday, 28 November, from 10 AM to 1 PM."


def timings_card():
    return ("\u23F0 School Timings\n\nMonday-Friday: 8:00 AM - 2:30 PM\nAssembly: 8:00 AM \u2022 Gates close 8:10 AM\n"
            "Saturday: closed, except PTM and events\n\nIf your child will be late, say 'report absence' or message the class teacher.")


def timings_spoken():
    return "School runs from 8 AM to 2:30 PM, Monday to Friday. The gates close at 8:10."


def uniform_card():
    return ("\U0001F454 Uniform Policy\n\nRegular (Mon-Thu): white shirt with navy trousers or skirt\n"
            "Sports (Fri & PE days): house t-shirt with track pants\nWinter (from 1 Nov): add the navy sweater\n\n"
            "Black leather shoes on regular days; white sports shoes on Fridays.")


def uniform_spoken():
    return ("Regular days need a white shirt with navy bottoms. Fridays are house t-shirt and track pants. "
            "The navy sweater is added from 1 November.")


def contacts_card():
    rows = "\n".join(f"\u2022 {k}: {v}" for k, v in CONTACTS.items())
    return f"\u260E\ufe0f School Contacts (Mon-Fri, 8 AM - 4 PM)\n\n{rows}\n\nPrefer a callback? Say 'talk to a person'."


def contacts_spoken():
    return "The school office is reachable on 0 4 4, 5 5 5, 0 1 4 2, between 8 AM and 4 PM on weekdays."


def transport_card(route=None):
    rows = "\n".join(f"\u2022 {r} ({a}) - pickup {p}, drop {d}" for r, (a, p, d) in ROUTES.items())
    if route and route in ROUTES:
        a, p, d = ROUTES[route]
        head = f"\U0001F68C {route} ({a})\nMorning pickup {p} \u2022 Afternoon drop {d}\n\nAll routes:\n"
    else:
        head = "\U0001F68C School Bus Routes\n\n"
    return head + rows + "\n\nLive tracking is not connected. For delays call the Transport desk."


def transport_spoken(route=None):
    if route and route in ROUTES:
        a, p, d = ROUTES[route]
        return f"{route} picks up at {p} and drops at {d}."
    return "We run Routes 4, 7 and 12. Ask me about a specific route for its timings."


def teachers_card():
    rows = "\n".join(f"\u2022 {n} ({s}) - {a}" for n, (s, a) in TEACHERS.items())
    return f"\U0001F469\u200D\U0001F3EB Teacher Availability\n\n{rows}\n\nSay 'meet a teacher' to request a slot."


def fee_structure_card(grade=None):
    rows = "\n".join(f"\u2022 {b}: {inr(t)} tuition per term" for b, t in FEE_BANDS)
    head = f"\U0001F4B0 Fee Structure - {grade}\n\n" if grade else "\U0001F4B0 Fee Structure\n\n"
    return (head + rows + f"\n\nEvery term also has Activities {inr(ACTIVITIES_FEE)} and Exam {inr(EXAM_FEE)}. "
            f"Transport is optional: Route 4 {inr(ROUTE_FEE['Route 4'])}, Route 7 {inr(ROUTE_FEE['Route 7'])}, "
            f"Route 12 {inr(ROUTE_FEE['Route 12'])}.")


def fee_due_card(grade=None):
    g = grade if grade else "your grade"
    return (f"\U0001F4B3 Fee Due Dates - {g}\n\nTuition fee for {g} is due on {TERM_DUE['Term 1']} (Term 1), "
            f"{TERM_DUE['Term 2']} (Term 2) and {TERM_DUE['Term 3']} (Term 3).\n\n"
            f"Grace period: {GRACE_DAYS} days \u2022 Late fee: {inr(LATE_FEE)}")


def fee_due_line(grade, fee_type="Tuition"):
    """Exact one-liner from the deck (slide 16): 'Tuition fee for Grade 5 is due on 15 Aug.'"""
    return f"{fee_type} fee for {grade} is due on {TERM_DUE['Term 1']}."


def fee_deadline_card():
    return (f"\u23F0 Next Fee Deadline\n\n{NEXT_TERM} fees are due on {TERM_DUE[NEXT_TERM]} 2026.\n"
            f"Grace period: {GRACE_DAYS} days (till 22 Nov). After that a late fee of {inr(LATE_FEE)} applies.\n\n"
            "Pay on the parent portal or at the fee office.")


def low_attendance_card():
    below = [s for s in STUDENTS.values() if att_days_needed(s)]
    near = [s for s in STUDENTS.values() if not att_days_needed(s) and att_pct(s) < 80]
    lines = [f"\u2022 {s['first']} - {att_pct(s)}% (needs {att_days_needed(s)} more days present in a row)" for s in below]
    body = "\n".join(lines) if lines else "\u2022 None"
    return ("\u26a0\ufe0f Attendance Alerts\n\nThe school requires 75% attendance.\n\n"
            f"Below 75%:\n{body}\n\nNear the limit (under 80%): {', '.join(s['first'] for s in near) or 'none'}\n\n"
            "If absences were medical, send a certificate to the class teacher.")


def attendance_history_card():
    rows = "\n".join(f"\u2022 {s['first']}: " + " \u2192 ".join(f"{m}%" for m in s["att_months"])
                     for s in STUDENTS.values())
    return (f"\U0001F4C5 Monthly Attendance (Jul \u2192 Oct)\n\n{rows}\n\nTap a child's name for the full report.")


def announcements_card(category=None):
    if category and category in ANNOUNCEMENTS:
        t, b = ANNOUNCEMENTS[category]
        return f"\U0001F4E2 {category} Announcement\n\n{t}\n{b}"
    rows = "\n".join(f"\u2022 [{c}] {t}" for c, (t, _) in ANNOUNCEMENTS.items())
    return f"\U0001F4E2 Latest Announcements\n\n{rows}\n\nPick a category for the full notice."


def admission_card():
    return ("\U0001F393 Admissions 2027-28\n\nApplications open: 1 Dec 2026 - 28 Feb 2027\n"
            "Documents: birth certificate, last report card, address proof, two photographs\n"
            "Process: enquiry form \u2192 document check \u2192 interaction \u2192 offer\n\n"
            f"Admissions desk: {CONTACTS['Admissions']}")


# ---------------------------------------------------------------------------
# Class-level attendance (term to date, whole grade) -- mock data.
# Separate from individual records: a grade has ~35 children, our demo holds a few of them,
# so the grade figure is its own stored number (it is NOT the mean of the demo children).
# Values are distinct per grade so each grade has its own one-line answer.
# ---------------------------------------------------------------------------
GRADE_ATTENDANCE = {1: 97, 2: 96, 3: 95, 4: 94, 5: 93, 6: 91, 7: 90, 8: 92, 9: 89, 10: 88, 11: 87, 12: 86}


def grade_attendance_pct(grade):
    return GRADE_ATTENDANCE.get(grade_number(grade))


def grade_attendance_line(grade):
    """The one-line grade answer, e.g. 'Attendance is 92% for this term.'"""
    pct = grade_attendance_pct(grade)
    return f"Attendance is {pct}% for this term." if pct is not None else None


# Quick-reply chips shown under each per-child card (shared by agent + webhook)
CARD_CHIPS = {
    "Attendance": ["Exam results", "Fees", "Homework", "Monthly trend", "Switch child", "Main menu"],
    "Results": ["Attendance", "Fees", "Homework", "Re-exam info", "Switch child", "Main menu"],
    "Fees": ["Fee deadline", "Fee receipt", "Attendance", "Switch child", "Main menu"],
    "Homework": ["Attendance", "Exam results", "Study material", "Due dates", "Switch child", "Main menu"],
}
