<p align="center">
  <img src="assets/banner.svg" alt="ParentConnect AI banner" width="100%">
</p>

<p align="center">
  <b>A multilingual Dialogflow ES assistant for parent–school communication, with an optional Python webhook.</b><br>
  Dialogflow ES agent · Flask webhook · English, Hindi and Tamil
</p>

<p align="center">
  <img alt="Dialogflow ES" src="https://img.shields.io/badge/Dialogflow-ES-orange">
  <img alt="Languages" src="https://img.shields.io/badge/languages-English%20%7C%20Hindi%20%7C%20Tamil-blue">
  <img alt="Webhook" src="https://img.shields.io/badge/webhook-Flask%20%2B%20Render-green">
  <img alt="Version" src="https://img.shields.io/badge/version-2.2-lightgrey">
</p>

<p align="center"><b>Live chatbot:</b> <a href="https://bot.dialogflow.com/5440aabf-6d36-4d59-b080-80fb57b6403c">https://bot.dialogflow.com/5440aabf-6d36-4d59-b080-80fb57b6403c</a></p>

---

## Table of Contents

- [Overview](#overview)
- [Problem and users](#problem-and-users)
- [What it can do](#what-it-can-do)
- [Repository structure](#repository-structure)
- [Quick start](#quick-start)
- [Agent configuration](#agent-configuration)
- [Intents](#intents)
- [Contexts](#contexts)
- [Entities](#entities)
- [Integration details](#integration-details)
- [Testing and optimization](#testing-and-optimization)
- [Webhook](#webhook)
- [Deploying the webhook on Render](#deploying-the-webhook-on-render)
- [Demo data](#demo-data)
- [Test checklist](#test-checklist)
- [Known issues](#known-issues)
- [Privacy and safety](#privacy-and-safety)
- [Contributing](#contributing)

---

## Overview

ParentConnect AI lets parents check their child's attendance, results, fees and homework, look up exam schedules, announcements, holidays and transport, and reach the right person at school, through plain language or by tapping quick-reply chips.

The project has two parts that work together:

1. **The Dialogflow ES agent** (`agent/`): intents, entities and replies in English, Hindi and Tamil. It works on its own with built-in replies.
2. **The webhook** (`webhook/`): a small Flask app that adds per-child memory, ticket IDs, optional PIN protection and call-transfer details.

> **Important:** All student names, IDs, grades and records in this repository are **fictional demo data**. Replace them with a real, secure backend before any production use.

## Problem and users

**The problem:** parents struggle to get quick, accurate information from school. Attendance, exam dates and fee dues sit in circulars and WhatsApp groups, teachers are hard to reach, and the school office answers the same questions again and again.

**Primary users**
- **Parents and guardians**, including households with more than one child at the school.
- **School staff** (front office, class teachers, accounts), who receive fewer repeat calls and get complaints, messages and meeting requests as structured requests.

**Pain points identified**
1. No easy way to see attendance without calling the office.
2. Exam schedules and fee deadlines are buried in circulars.
3. Announcements get lost across messaging groups.
4. Teachers are hard to reach, and meeting requests are manual.
5. Communication is one-way: the school broadcasts, and parents can rarely ask a quick question.

**Chatbot goals:** quick access to attendance, exam schedules and results, fee details, announcements and homework; contact with teachers and the office; a safe hand-off to a human when the bot can't help.

**Scope:** a Dialogflow ES agent answering these queries in English, Hindi and Tamil, with an optional webhook. Demo data only; it does not connect to a real school system.

## What it can do

| Area | Examples |
|---|---|
| Student records | Attendance, results, fees and homework for each child |
| Attendance | Monthly history, low-attendance alerts, report an absence with a reason |
| Exams | Exam schedule, syllabus, re-exam information |
| Fees | Fee structure, fee status, due dates, payment deadlines, receipts |
| School info | Timings, holidays, uniform policy, transport routes, events calendar |
| Announcements | Academic, general, event and urgent notices |
| Teachers | Availability, request a meeting, message a teacher, parent-teacher meetings |
| Support | Complaints, feedback, service rating, hand-off to a human |
| Languages | English, Hindi, Tamil |

## Repository structure

```
ParentConnectAI/
├── agent/                      Dialogflow ES agent export (zip the contents to import)
│   ├── agent.json
│   ├── package.json
│   ├── intents/                85 intents plus their training-phrase files
│   └── entities/               20 entities
├── assets/
│   └── banner.svg              README header banner
├── webhook/                    Flask fulfillment service
│   ├── webhook.py
│   ├── school_data.py          demo school and student data
│   └── requirements.txt
└── README.md
```

## Quick start

### 1. Import the agent

1. Zip the **contents** of the `agent/` folder, so `agent.json` sits at the root of the zip and not inside a subfolder.
2. Open the [Dialogflow ES console](https://dialogflow.cloud.google.com/).
3. Go to **Settings → Export and Import**.
4. Choose **Restore from ZIP** to replace the current draft, or **Import from ZIP** to merge.
5. Train the agent and try it in the simulator.

> **Caution:** Restore from ZIP overwrites the current agent draft. Export a backup first if the target agent already has work in it.

### 2. Connect the webhook (optional)

The webhook is enabled on 53 intents. If you do **not** host it, those intents still answer from their built-in replies, but each one waits for the webhook call to fail first, which makes replies slower. Either deploy the webhook (see [below](#deploying-the-webhook-on-render)) or turn off `webhookUsed` on those intents.

## Agent configuration

Defined in `agent/agent.json`:

| Setting | Value |
|---|---|
| Default language | English (`en`) |
| Supported languages | Hindi (`hi`), Tamil (`ta`) |
| Default timezone | Asia/Kolkata |
| ML minimum confidence | 0.3 |
| Webhook URL | Placeholder (`https://YOUR-HOST.example.com/webhook`). Replace it with your own |

## Intents

85 intents in total, grouped by feature.

### Core navigation
`Default Welcome Intent`, `Default Fallback Intent`, `MainMenuIntent`, `MoreMenuIntent`, `Help`, `About ParentConnect AI`, `ThankYouIntent`, `GoodbyeIntent`

### Student selection and per-child flows
- `ChooseStudentIntent` and `Select Aarav / Diya / Kabir / Ishita`
- For each of the four children, four intents: **Attendance, Results, Fees, Homework** (`Aarav - Attendance`, and so on)
- The same four again as **`Active <name> - ...`** intents, which fire when a child is already selected and the parent just says "fees" or "homework"

That is 36 intents for the four children.

### Attendance
`AttendanceIntent`, `AttendanceHistoryIntent`, `GradeAttendanceIntent`, `LowAttendanceAlertIntent`, `SubmitAbsenceReasonIntent`

### Exams and academics
`ResultsIntent`, `ExamScheduleIntent`, `ReExamIntent`, `SyllabusIntent`, `HomeworkIntent`, `AssignmentDeadlineIntent`, `StudyMaterialIntent`

### Fees
`FeeStructureIntent`, `FeeStatusIntent`, `FeeDueIntent`, `FeePaymentDeadlineIntent`, `FeeReceiptIntent`

### Announcements and school info
`LatestAnnouncementIntent`, `AnnouncementAcademicIntent`, `AnnouncementGeneralIntent`, `AnnouncementEventIntent`, `AnnouncementUrgentIntent`, `SchoolTimingsIntent`, `HolidayListIntent`, `EventCalendarIntent`, `UniformPolicyIntent`, `TransportRouteIntent`, `AdmissionEnquiryIntent`, `ContactInfoIntent`

### Teachers and meetings
`TeacherAvailabilityIntent`, `RequestMeetingIntent`, `MessageTeacherIntent`, `PTMScheduleIntent`

### Support and feedback
`HumanEscalationIntent`, `ComplaintRegistrationIntent`, `ComplaintDetailsIntent`, `FeedbackSubmissionIntent`, `FeedbackCaptureIntent`, `ServiceRatingIntent`, `ParentVerificationIntent`

## Contexts

| Context | Purpose |
|---|---|
| `student-aarav`, `student-diya`, `student-kabir`, `student-ishita` | Remember which child the parent selected, so later messages like "fees" go straight to the right child |
| `awaiting-details` | Waiting for the details of a complaint |
| `awaiting-feedback` | Waiting for the parent's feedback text |
| `parent-verified` | Set by the webhook after a correct PIN (used when verification is turned on) |

`ChooseStudentIntent` and `MainMenuIntent` clear the `student-*` contexts, so a previously selected child is never carried into a new selection.

## Entities

20 custom entities: `AbsenceReason`, `AnnouncementCategory`, `AttendanceStatus`, `ComplaintCategory`, `ContactType`, `DateEntity`, `DayOfWeek`, `DocumentType`, `EventType`, `ExamType`, `FeeType`, `FeedbackType`, `GradeAttendance`, `GradeClass`, `StudentId`, `StudentName`, `Subject`, `TeacherName`, `Term`, `TransportRoute`.

### What each entity does

| Entity | Purpose |
|---|---|
| `StudentName`, `StudentId` | Identify which child a question is about |
| `GradeClass`, `GradeAttendance` | Recognise a grade or class ("Grade 8", "class 8"). `GradeAttendance` maps it to that grade's attendance reply |
| `Subject`, `TeacherName` | Pick the subject or teacher for homework, syllabus, messages and meetings |
| `Term`, `ExamType` | Term and exam type (unit test, midterm, final) for schedules and results |
| `FeeType` | Which fee a question is about |
| `DateEntity`, `DayOfWeek` | Dates and days, including relative ones like "tomorrow" |
| `AbsenceReason`, `AttendanceStatus` | Why a child was absent, and attendance state for alerts |
| `AnnouncementCategory`, `EventType` | Filter announcements and events |
| `TransportRoute` | Bus route lookups |
| `ContactType` | Who the parent wants to reach (office, principal, transport and so on) |
| `DocumentType` | Receipts and study material |
| `ComplaintCategory`, `FeedbackType` | Classify complaints and feedback |

Required slots such as the child, the reason for an absence, or the teacher have prompts, so the bot asks for anything missing before it answers (for example, "Which child is this about?"). This is set up on 11 intents, including `SubmitAbsenceReasonIntent`, `FeeDueIntent`, `GradeAttendanceIntent`, `RequestMeetingIntent`, `MessageTeacherIntent` and `ComplaintRegistrationIntent`.

## Integration details

| Piece | How it is used |
|---|---|
| **Dialogflow ES agent** | The chatbot itself: 85 intents, 20 entities, contexts, quick replies and rich-content chips |
| **Dialogflow Web Demo** | The live chatbot link at the top of this page, which can also be embedded as an `<iframe>` |
| **Dialogflow Messenger** | Optional chat widget for a web page, and where the chips render best |
| **Webhook (Flask on Render)** | Fulfillment for 53 intents: per-child memory, ticket IDs, PIN checks, confidence gate |
| **GitHub** | Stores the agent export and the webhook code, and hosts this documentation |

Every intent also has built-in replies, so the agent still answers if the webhook is switched off.

## Webhook

Fulfillment is handled by `webhook/webhook.py`, a Flask app with two routes:

| Route | Purpose |
|---|---|
| `POST /webhook` | Dialogflow fulfillment endpoint |
| `GET /health` | Health check, returns `status: ok` |

**What the webhook adds on top of the built-in replies:**

- Remembers the selected child across turns
- Generates ticket IDs for complaints, messages and meeting requests
- Optional PIN protection for personal records
- Call-transfer details for the "Human help" path
- Asks the parent to rephrase when intent confidence is below 0.7
- Skips Hindi and Tamil requests, which keep using the agent's built-in replies

**Environment variables:**

| Variable | Default | Meaning |
|---|---|---|
| `PC_REQUIRE_VERIFICATION` | off | Set to `1` to require "verify me" and a PIN before showing personal records |
| `PC_DEMO_PIN` | `1234` | The demo PIN. Change it before sharing the service |
| `PC_CONFIDENCE_GATE` | `0.7` | Confidence below this asks the parent to rephrase |

**Run locally:**

```bash
cd webhook
pip install -r requirements.txt
python webhook.py
# or: gunicorn webhook:app --bind 0.0.0.0:8080
```

## Deploying the webhook on Render

1. Push this repository to GitHub.
2. In Render, choose **New → Web Service** and connect the repository.
3. Use these settings:

   | Setting | Value |
   |---|---|
   | Language | Python 3 |
   | Root Directory | `webhook` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `gunicorn webhook:app` |

4. Add the environment variables you want (see the table above).
5. After the deploy finishes, open `https://YOUR-SERVICE.onrender.com/health` and check it returns `status: ok`.
6. In Dialogflow, go to **Fulfillment**, enable **Webhook**, and set the URL to `https://YOUR-SERVICE.onrender.com/webhook`.

> **Free-tier note:** Render's free instances sleep after a period of inactivity, and the first request can take 30 to 60 seconds. Dialogflow gives up after about 5 seconds, so the first message after a quiet period may fall back to the built-in reply. Open `/health` shortly before a demo to wake the service.

## Demo data

Four fictional students are defined in `webhook/school_data.py` and mirrored in the agent's built-in replies:

| Student | Grade |
|---|---|
| Aarav | Grade 8 |
| Diya | Grade 5 |
| Kabir | Grade 6 |
| Ishita | Grade 8 |

Attendance, results, fees, homework, the exam timetable, holidays, timings and contacts are all hardcoded sample data.

## Testing and optimization

**Unit testing:** every intent has 10 or more English training phrases (84 of 85; only the default fallback has none by design), and each was written with varied wording. **Integration testing** uses end-to-end journeys in the Dialogflow simulator. Run each scenario below and record the result.

| # | User says (journey) | Expected reply | Result |
|---|---|---|---|
| 1 | "Show attendance for Grade 8" | "Attendance is 92% for this term." | ☐ Pass ☐ Fail |
| 2 | "Choose student" → "Aarav" → "attendance" | Aarav Sharma's attendance card: 92 of 100 days (92%), status Excellent | ☐ Pass ☐ Fail |
| 3 | "When is the fee due for Grade 8?" | "Tuition fee for Grade 8 is due on 15 Aug." | ☐ Pass ☐ Fail |
| 4 | "When are the exams?" | Exam schedule card: midterm done, final exams 2–11 Dec 2026 | ☐ Pass ☐ Fail |
| 5 | "My child was absent due to fever" | Bot asks "Which child is this about?", then confirms the absence is noted | ☐ Pass ☐ Fail |
| 6 | "What are the school timings?" | Timings card: Mon–Fri, 8:00 AM – 2:30 PM, with chips | ☐ Pass ☐ Fail |
| 7 | "I want to talk to the school office" | Hand-off message with the office number | ☐ Pass ☐ Fail |
| 8 | "What is the capital of France?" | Fallback: "Sorry, I didn't catch that..." with option chips | ☐ Pass ☐ Fail |

**Issues found and fixed during testing**

| Issue | Fix |
|---|---|
| A previously selected child stayed active after going back to the menu, so a parent could see the wrong child's data | `ChooseStudentIntent` and `MainMenuIntent` now clear the student contexts |
| Import failed: some Tamil quick-reply buttons were over Dialogflow's 20-character limit | Buttons shortened, and the new text added as training phrases |
| Attendance trend and absence reports skipped the PIN check when verification was on | PIN check added to both |
| The same generic phrases ("attendance", "fees") appear in the plain and per-child intents | Intended design: the per-child "Active" intents only match while that child's context is active, and the plain intent handles the rest |
| 53 intents called a webhook URL that didn't exist, slowing replies | Webhook deployed on Render, with the built-in replies as backup |

To keep improving accuracy, check **Training → History** in Dialogflow for phrases that hit the fallback and add them as training phrases to the right intent.

## Test checklist

After importing, check the following:

- [ ] "hello" triggers `Default Welcome Intent`
- [ ] An unrelated phrase triggers `Default Fallback Intent`
- [ ] Choosing a student, then saying "fees", shows that child's fees
- [ ] Going to the main menu and choosing another child does not show the previous child's data
- [ ] Hindi and Tamil replies appear when the language is switched
- [ ] Quick-reply buttons work in Dialogflow Messenger (each button text is 20 characters or fewer)
- [ ] `GET /health` returns `status: ok` once the webhook is deployed
- [ ] With `PC_REQUIRE_VERIFICATION=1`, personal records stay locked until "verify me" and a correct PIN
- [ ] Dialogflow reports no validation or training errors

## Known issues

- **Shared training phrases:** generic phrases like "attendance" appear in both the plain intent and the per-child "Active" intents. This is by design and relies on contexts. It only misroutes if two children's contexts are active at once, which the context reset prevents.
- **Placeholder values:** the transfer phone numbers in `webhook.py` are fake, the demo PIN is `1234`, and the agent's webhook URL is a placeholder.
- **Hardcoded data:** all records are static sample text, not live data.
- **Past fee dates:** some fee due dates in the sample data are already in the past.
- **Hindi and Tamil:** these languages use the built-in replies only and do not get the webhook extras.
- **Quick-reply limit:** Dialogflow rejects quick-reply buttons longer than 20 characters. Keep new buttons under that limit, especially in Tamil.

## Privacy and safety

- Do not commit service-account JSON files, API keys, access tokens or real student records.
- Set secrets such as `PC_DEMO_PIN` as environment variables on the host, not in the code.
- Use a **private** repository if you change the demo data or PIN to anything real.
- Avoid collecting sensitive student information through free-text messages.
- Review Dialogflow interaction-log settings against the school's privacy requirements before public deployment.
- Provide a human contact for high-impact questions.

## Contributing

When adding an intent, include varied training phrases in every supported language, keep quick-reply buttons within 20 characters, and add a path back to the main menu or to human support. Test in the Dialogflow ES simulator before exporting an updated agent.

---

_Built to make parent-school communication simpler and more accessible._
