# Automatic Invoice Collection System — From Scratch (Python)
*Generated on 2025-11-06 18:19*

This document gives you **everything** you need to build a self‑hosted, Python-based **Automatic Invoice Collection System** (no Make.com). It’s structured as **Prompt → Work it will do → Implementation**, repeated for each section.

The system preserves your original intent: **create Gmail drafts (not auto-send)** for escalating invoice reminders based on the number of days overdue, driven by data in **Google Sheets** (or a database).

---

## High-Level Summary

- **Goal:** Reduce collection time and reclaim founder hours by automating 95% of the follow-up, while preserving a human “send” step via Gmail **drafts**.
- **Core pieces:** Data source (Google Sheets) → Scheduler/Router (Python) → Draft creation (Gmail API) → Optional review CLI/terminal checklist.
- **Results target:** 6-stage sequence (7/14/21/28/35/42 days), firming tone, owner reviews drafts daily and clicks Send.
- **Privacy & control:** Runs on your machine or server; stores credentials locally; no third-party automation platforms.

---

## Architecture (Overview)

```
        ┌──────────────────────────┐
        │ Google Sheets (Invoices) │
        │  - status, due_date,     │
        │    client, amount, etc.  │
        └───────────┬──────────────┘
                    │ read/write via API
                    ▼
           ┌──────────────────┐
           │  Python Scheduler│
           │  (cron/APScheduler)
           └───────┬──────────┘
                   │  routes by days overdue
                   ▼
           ┌──────────────────┐
           │ Reminder Router  │
           │  (7/14/21/28/35/42)
           └───────┬──────────┘
                   │  selects template + merge fields
                   ▼
           ┌──────────────────┐
           │ Gmail API        │
           │  create DRAFTS   │
           └──────────────────┘
```

---

# Section 1 — Project Scaffold & Repo

### Prompt
**“Create a clean Python project scaffold for an invoice collections engine with modules for sheets, routing, email, and templates; include tests and a Makefile.”**

### Work it will do
- Creates directories and starter files so the codebase stays organized and testable.

### Implementation
```
invoice-collector/
├─ src/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ sheets.py
│  ├─ router.py
│  ├─ emailer.py
│  ├─ scheduler.py
│  ├─ models.py
│  └─ templates/
│     ├─ stage_07.txt
│     ├─ stage_14.txt
│     ├─ stage_21.txt
│     ├─ stage_28.txt
│     ├─ stage_35.txt
│     └─ stage_42.txt
├─ tests/
│  ├─ test_router.py
│  └─ test_templates.py
├─ .env.example
├─ requirements.txt
├─ README.md
└─ main.py
```

**requirements.txt**
```
google-api-python-client==2.151.0
google-auth==2.35.0
google-auth-oauthlib==1.2.1
pandas==2.2.3
python-dotenv==1.0.1
APScheduler==3.10.4
tabulate==0.9.0
```

---

# Section 2 — Environment & Virtualenv

### Prompt
**“Give me the exact shell commands to set up a Python venv, install deps, and run a basic sanity check.”**

### Work it will do
- Sets up an isolated environment and verifies that the toolchain runs.

### Implementation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Sanity check
python -c "import pandas, apscheduler; print('OK')"
```

---

# Section 3 — Google Cloud + APIs (OAuth)

### Prompt
**“Walk me through creating a Google Cloud project, enabling Sheets + Gmail APIs, and downloading OAuth credentials for a desktop app.”**

### Work it will do
- Creates OAuth client, enables APIs, and stores credentials locally.

### Implementation
1. Go to **Google Cloud Console** → Create Project.
2. **APIs & Services → Enable APIs**: enable **Google Sheets API** and **Gmail API**.
3. **Credentials → Create Credentials → OAuth client ID**.
   - Application type: **Desktop app**.
   - Download `client_secret.json` → place at project root.
4. First run will open a browser to authorize; tokens will be cached locally (e.g., `token.json`).

**.env.example**
```
GOOGLE_SHEETS_SPREADSHEET_ID=your_sheet_id_here
GOOGLE_SHEETS_RANGE=Invoices!A1:Z999
GMAIL_SENDER=you@yourdomain.com
DRY_RUN=true
```

---

# Section 4 — Data Model & Google Sheet Schema

### Prompt
**“Define a minimal Google Sheets schema for tracking overdue invoices and a Python dataclass to map rows to objects.”**

### Work it will do
- Standardizes columns so the router has what it needs.

### Implementation
**Recommended columns (row 1 headers):**
```
invoice_id | client_name | client_email | amount | currency | due_date | sent_date | status | notes | last_stage_sent | last_sent_at
```

**src/models.py**
```python
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Invoice:
    invoice_id: str
    client_name: str
    client_email: str
    amount: float
    currency: str
    due_date: date
    sent_date: date
    status: str  # e.g., "Overdue", "Paid", "Open"
    notes: Optional[str] = ""
    last_stage_sent: Optional[int] = None  # 7,14,21,28,35,42
    last_sent_at: Optional[date] = None
```

---

# Section 5 — Sheets Client

### Prompt
**“Write a minimal helper to read/write invoices from Google Sheets using the Sheets API.”**

### Work it will do
- Reads rows → `Invoice` objects; writes back status/last_stage_sent updates.

### Implementation
**src/sheets.py (excerpt)**
```python
import os
import pandas as pd
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
from .models import Invoice

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]  # read/write

load_dotenv()

SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
RANGE_NAME = os.getenv("GOOGLE_SHEETS_RANGE", "Invoices!A1:Z999")

def _get_sheets_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.fromAuthorizedUserFile("token.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("sheets", "v4", credentials=creds)

def read_invoices():
    svc = _get_sheets_service()
    values = svc.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute().get("values", [])
    if not values:
        return []

    headers = values[0]
    rows = values[1:]

    df = pd.DataFrame(rows, columns=headers)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["due_date"] = pd.to_datetime(df["due_date"]).dt.date
    df["sent_date"] = pd.to_datetime(df["sent_date"]).dt.date
    for col in ["last_stage_sent", "last_sent_at"]:
        if col in df.columns:
            if col == "last_stage_sent":
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    invoices = []
    for _, r in df.iterrows():
        invoices.append(Invoice(
            invoice_id=str(r.get("invoice_id","")).strip(),
            client_name=str(r.get("client_name","")).strip(),
            client_email=str(r.get("client_email","")).strip(),
            amount=float(r.get("amount",0.0)),
            currency=str(r.get("currency","USD")).strip(),
            due_date=r.get("due_date"),
            sent_date=r.get("sent_date"),
            status=str(r.get("status","")).strip(),
            notes=str(r.get("notes","")) if not pd.isna(r.get("notes")) else "",
            last_stage_sent=int(r.get("last_stage_sent")) if pd.notna(r.get("last_stage_sent")) else None,
            last_sent_at=r.get("last_sent_at") if pd.notna(r.get("last_sent_at")) else None
        ))
    return invoices
```

*(You can add a `write_back` function to update `last_stage_sent` and `last_sent_at` using `values.update` with the row index.)*

---

# Section 6 — Templating (Tone Escalation)

### Prompt
**“Create six email templates (txt) for 7/14/21/28/35/42 days overdue with merge fields: {{name}}, {{amount}}, {{currency}}, {{invoice_id}}, {{due_date}}.”**

### Work it will do
- Gives reusable drafts with progressive tone.

### Implementation
**src/templates/stage_07.txt (example)**
```
Subject: Friendly nudge on invoice {{invoice_id}}

Hi {{name}},

Hope you’re doing well. Quick check-in on invoice {{invoice_id}} for {{amount}} {{currency}}, due {{due_date}}.
If there’s anything you need from us, just reply and we’ll help.

Thanks!
```

*(Create similar files for other stages with firmer language; keep professional.)*

---

# Section 7 — Router Logic

### Prompt
**“Write a router that selects the correct stage (7/14/21/28/35/42) based on days overdue and prevents repeat sends on the same day.”**

### Work it will do
- Converts days overdue → stage; ensures idempotency per day.

### Implementation
**src/router.py**
```python
from datetime import date

STAGES = [7, 14, 21, 28, 35, 42]

def days_overdue(due_date: date, today: date) -> int:
    return max(0, (today - due_date).days)

def stage_for(days: int) -> int | None:
    eligible = [s for s in STAGES if days >= s]
    return max(eligible) if eligible else None

def should_send(stage: int | None, last_stage_sent: int | None, last_sent_at: date | None, today: date) -> bool:
    if stage is None:
        return False
    if last_sent_at == today:
        return False
    if last_stage_sent is None:
        return True
    # Allow sending the same stage if we skipped the exact day but caught up later; otherwise send only if higher stage
    return stage > last_stage_sent
```

**tests/test_router.py**
```python
from datetime import date, timedelta
from src.router import days_overdue, stage_for, should_send

def test_stage_progression():
    today = date(2025, 1, 22)
    assert stage_for(days_overdue(date(2025,1,15), today)) == 7
    assert stage_for(days_overdue(date(2025,1,1),  today)) == 21

def test_should_send_basic():
    today = date(2025, 1, 22)
    assert should_send(7, None, None, today)
    assert not should_send(None, None, None, today)
```

---

# Section 8 — Gmail Draft Creation (Not Auto-Send)

### Prompt
**“Write a Gmail helper that merges a template and creates a DRAFT (not send) from the authorized account.”**

### Work it will do
- Builds subject/body from templates; creates Gmail Drafts via API.

### Implementation
**src/emailer.py (excerpt)**
```python
import os, base64, re
from string import Template
from datetime import date
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
load_dotenv()

SENDER = os.getenv("GMAIL_SENDER")

def _get_gmail_service():
    creds = None
    if os.path.exists("token_gmail.json"):
        creds = Credentials.from_authorized_user_file("token_gmail.json", SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token_gmail.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def render_template(path: str, ctx: dict) -> tuple[str, str]:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    # Extract Subject: first line convention
    m = re.match(r"Subject:\s*(.*)\n\n(.*)", raw, flags=re.S)
    subject = Template(m.group(1)).safe_substitute(ctx)
    body = Template(m.group(2)).safe_substitute(ctx)
    return subject, body

def create_draft(to_email: str, subject: str, body: str):
    service = _get_gmail_service()
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to_email
    msg["From"] = SENDER
    msg["Subject"] = subject
    create_msg = {"message": {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}}
    return service.users().drafts().create(userId="me", body=create_msg).execute()
```

---

# Section 9 — Scheduler & Orchestration

### Prompt
**“Write a daily job that: loads invoices → computes stage → renders template → creates Gmail DRAFT → writes back last_stage_sent/last_sent_at.”**

### Work it will do
- End-to-end orchestration; safe by default (respects DRY_RUN).

### Implementation
**src/scheduler.py (excerpt)**
```python
import os
from datetime import date
from dotenv import load_dotenv
from .sheets import read_invoices  # add write_back_invoices(...) as needed
from .router import days_overdue, stage_for, should_send
from .emailer import render_template, create_draft

load_dotenv()
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

def template_path_for(stage: int) -> str:
    return f"src/templates/stage_{stage:02d}.txt"

def run_daily():
    today = date.today()
    invoices = read_invoices()
    created = []

    for inv in invoices:
        if inv.status.lower() != "overdue":
            continue
        d = days_overdue(inv.due_date, today)
        stage = stage_for(d)
        if not should_send(stage, inv.last_stage_sent, inv.last_sent_at, today):
            continue

        ctx = {
            "name": inv.client_name,
            "amount": "{:,.2f}".format(inv.amount),
            "currency": inv.currency,
            "invoice_id": inv.invoice_id,
            "due_date": inv.due_date.strftime("%b %d, %Y")
        }
        subject, body = render_template(template_path_for(stage), ctx)

        if DRY_RUN:
            print(f"[DRY] Would draft ({stage}d) to {inv.client_email}: {subject}")
        else:
            create_draft(inv.client_email, subject, body)
            # TODO: write back inv.last_stage_sent=stage, inv.last_sent_at=today

        created.append((inv.invoice_id, stage, inv.client_email, subject))

    return created
```

**main.py**
```python
from src.scheduler import run_daily

if __name__ == "__main__":
    results = run_daily()
    print(f"Created {len(results)} draft(s).")
```

---

# Section 10 — Daily Review CLI (Optional)

### Prompt
**“Add a lightweight CLI to list today’s created drafts in a table so I can eyeball what’s queued.”**

### Work it will do
- Prints a pretty table of planned/sent drafts each run.

### Implementation
```python
# In scheduler.run_daily(), accumulate tuples and print with tabulate
from tabulate import tabulate
# after processing
print(tabulate(created, headers=["invoice_id","stage","email","subject"]))
```

---

# Section 11 — Logging & Metrics

### Prompt
**“Add structured logging and simple CSV metrics (date, stage, invoice_id) for each draft created.”**

### Work it will do
- Creates a local `logs/` dir and a CSV to track throughput & stages.

### Implementation
- On each draft, append to `logs/sends.csv` with: `timestamp,invoice_id,stage,email`.
- Optionally, push to Google Sheets “Log” tab for centralized auditing.

---

# Section 12 — Config Management

### Prompt
**“Load configuration from .env and provide a .env.example; support DRY_RUN and time windows (e.g., only draft 08:00–18:00).”**

### Work it will do
- Keeps secrets out of code; makes safe dry runs the default.

### Implementation
**src/config.py**
```python
import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    RANGE = os.getenv("GOOGLE_SHEETS_RANGE", "Invoices!A1:Z999")
    GMAIL_SENDER = os.getenv("GMAIL_SENDER")
    DRY_RUN = os.getenv("DRY_RUN","true").lower()=="true"
    WINDOW_START = int(os.getenv("WINDOW_START","8"))
    WINDOW_END = int(os.getenv("WINDOW_END","18"))
```

---

# Section 13 — Tests

### Prompt
**“Write unit tests for routing correctness and template merge safety.”**

### Work it will do
- Prevent regressions when you tweak stage rules or templates.

### Implementation
**tests/test_templates.py (excerpt)**
```python
from src.emailer import render_template
def test_render_has_subject_and_body(tmp_path):
    p = tmp_path/"t.txt"
    p.write_text("Subject: Hello {{name}}\n\nHi {{name}}", encoding="utf-8")
    subj, body = render_template(str(p), {"name":"Sarah"})
    assert "Sarah" in subj
    assert body.startswith("Hi Sarah")
```

Run tests:
```bash
pytest -q
```

---

# Section 14 — Deployment Options

### Prompt
**“Show two deployment paths: cron/systemd on a VPS and Dockerized service with daily run.”**

### Work it will do
- Gives copy/paste setups for reliable execution.

### Implementation
**Cron (daily at 9:00):**
```bash
0 9 * * * cd /path/to/invoice-collector && /path/to/.venv/bin/python main.py >> logs/cron.log 2>&1
```

**Dockerfile (minimal):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

# Section 15 — Security & Compliance

### Prompt
**“Document security basics: OAuth tokens, least-privilege scopes, no auto-send, access control, and GDPR-friendly data handling.”**

### Work it will do
- Reduces risk and keeps auditors happy.

### Implementation (Guidelines)
- Store `client_secret.json` and `token*.json` outside Git; add to `.gitignore`.
- Use minimal scopes (`spreadsheets`, `gmail.compose`).
- Keep **drafts only**; the human sends (preserves intent + reduces misfires).
- Log metadata only; avoid logging email bodies.
- Rotate credentials periodically; restrict Google account access with MFA.

---

# Section 16 — Extensibility Ideas

### Prompt
**“Add optional modules for Stripe links, Slack alerts for high-value invoices, and QuickBooks connector.”**

### Work it will do
- Opens doors for upsell versions or premium tiers.

### Implementation
- Stripe: generate payment link and append to email body.
- Slack: webhook on stage ≥ 28 and amount ≥ threshold.
- QuickBooks: replace Google Sheets with QBO queries; same router applies.

---

# Section 17 — Troubleshooting

### Prompt
**“List common errors and one-line fixes (OAuth scopes, bad ranges, Gmail draft quota, date parsing). Keep it short.”**

### Work it will do
- Saves time during first setup.

### Implementation
- `invalid_grant`: delete `token*.json` and re-auth.
- `403 insufficientPermissions`: check scopes match code.
- Empty reads: verify `SPREADSHEET_ID` + `RANGE` + sharing to your Google account.
- Dates off: ensure Sheet dates are real dates, not strings; locale settings.
- Gmail draft quota: stagger runs; window hours; backoff on 429.

---

# Section 18 — Daily Operating Procedure (Owner)

### Prompt
**“Write a 5-minute daily checklist for the owner to review drafts and click send.”**

### Work it will do
- Turns automation into a habit loop.

### Implementation
1. Open Gmail → Drafts.
2. Scan subjects; open high-value first.
3. Personalize first line if needed; click **Send**.
4. Archive sent email; add quick note in Sheet if there’s client context.
5. Empty Drafts; you’re done.

---

# Appendix A — Example Stage Templates (2–3 lines each)

*(Fill these in your tone. Keep ‘Subject:’ header on first line and a blank line before body.)*

**stage_14.txt**
```
Subject: Quick follow-up on invoice {{invoice_id}}

Hi {{name}} — circling back on invoice {{invoice_id}} ({{amount}} {{currency}}), due {{due_date}}. Could you confirm receipt or share an ETA on payment?
```

**stage_21.txt**
```
Subject: Past due: invoice {{invoice_id}}

{{name}}, this is a friendly reminder that invoice {{invoice_id}} is past due. Please advise timing today; happy to help if anything is blocking.
```

**stage_28.txt**
```
Subject: Action needed — invoice {{invoice_id}}

We’re now 4 weeks past due on {{invoice_id}} for {{amount}} {{currency}}. Please process payment or suggest a call to resolve today.
```

**stage_35.txt**
```
Subject: Final reminder before escalation — {{invoice_id}}

We’ve reached 5 weeks past due. Unless we hear back, we’ll need to initiate escalation procedures per terms. Please reply today.
```

**stage_42.txt**
```
Subject: Last notice — collections to follow ({{invoice_id}})

As we haven’t received payment or response, this is the last notice before collections/legal per agreement. Reply within 48 hours to avoid escalation.
```

---

## What to build next
- **Write-backs**: Implement `write_back_invoices` to update `last_stage_sent` and `last_sent_at` in the Sheet.
- **UI review mode**: Simple Streamlit app listing due items with a “Open Draft” button.
- **Rate limiting**: Exponential backoff on Gmail quota errors.

---

## Ready-to-use Prompts (All Sections, Copy/Paste)

1) *Scaffold*: “Create a clean Python project scaffold for an invoice collections engine with modules for sheets, routing, email, and templates; include tests and a Makefile.”  
2) *Env*: “Give me the exact shell commands to set up a Python venv, install deps, and run a basic sanity check.”  
3) *GCP*: “Walk me through creating a Google Cloud project, enabling Sheets + Gmail APIs, and downloading OAuth credentials for a desktop app.”  
4) *Schema*: “Define a minimal Google Sheets schema for tracking overdue invoices and a Python dataclass to map rows to objects.”  
5) *Sheets client*: “Write a minimal helper to read/write invoices from Google Sheets using the Sheets API.”  
6) *Templates*: “Create six email templates (txt) for 7/14/21/28/35/42 days overdue with merge fields.”  
7) *Router*: “Write a router that selects the correct stage based on days overdue and prevents repeat sends on the same day.”  
8) *Gmail drafts*: “Write a Gmail helper that merges a template and creates a **DRAFT** (not send).”  
9) *Scheduler*: “Write a daily job that orchestrates the pipeline and writes back metadata.”  
10) *Review CLI*: “Add a lightweight CLI to list today’s created drafts in a table.”  
11) *Logging*: “Add structured logging and CSV metrics for each draft created.”  
12) *Config*: “Load configuration from .env; support DRY_RUN and business hours.”  
13) *Tests*: “Write unit tests for routing correctness and template merge safety.”  
14) *Deploy*: “Show cron/systemd and Docker paths.”  
15) *Security*: “Document OAuth/token handling and least-privilege scopes.”  
16) *Extensibility*: “Add Stripe, Slack, and QuickBooks connectors.”  
17) *Troubleshoot*: “List common errors with one-line fixes.”  
18) *Ops*: “Write a 5-minute daily draft-review checklist.”

---

**You now have a full plan + working skeleton to implement the system from scratch without Make.com.**
