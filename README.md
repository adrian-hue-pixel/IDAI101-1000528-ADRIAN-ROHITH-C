<p align="center"> <img src="assets/banner.svg" alt="ParentConnect AI banner" width="100%"> </p> <p align="center"> <b>A multilingual Dialogflow ES assistant for parent–school communication, with an optional Python webhook.</b><br> Dialogflow ES agent · Flask webhook · English, Hindi and Tamil </p> <p align="center"> <img alt="Dialogflow ES" src="https://img.shields.io/badge/Dialogflow-ES-orange"> <img alt="Languages" src="https://img.shields.io/badge/languages-English%20%7C%20Hindi%20%7C%20Tamil-blue"> <img alt="Webhook" src="https://img.shields.io/badge/webhook-Flask%20%2B%20Render-green"> <img alt="Version" src="https://img.shields.io/badge/version-2.2-lightgrey"> </p> <p align="center">Chatbot link: <i>https://github.com/adrian-hue-pixel/SA-chatbot-1000528</i></p>

![Dialogflow ES](https://img.shields.io/badge/Dialogflow-ES-orange)
![Languages](https://img.shields.io/badge/languages-English%20%7C%20Hindi%20%7C%20Tamil-blue)
![Webhook](https://img.shields.io/badge/webhook-Flask%20%2B%20Render-green)
![Version](https://img.shields.io/badge/version-2.2-lightgrey)

---

## Table of Contents

- [Overview](#overview)
- [What it can do](#what-it-can-do)
- [Repository structure](#repository-structure)
- [Quick start](#quick-start)
- [Agent configuration](#agent-configuration)
- [Intents](#intents)
- [Contexts](#contexts)
- [Entities](#entities)
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
2. **The webhook** (`webhook/`): a small Flask app that adds per-child memory, ticket IDs, optional PIN protection, voice (SSML) output and call transfer.

> **Important:** All student names, IDs, grades and records in this repository are **fictional demo data**. Replace them with a real, secure backend before any production use.

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
- Voice (SSML) output and call transfer
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

- **Duplicate training phrases:** about 162 training phrases appear identically in different intents, so some messages can be routed to the wrong intent. Review and merge them.
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
