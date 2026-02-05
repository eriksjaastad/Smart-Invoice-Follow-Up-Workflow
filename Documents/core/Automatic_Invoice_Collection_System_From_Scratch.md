# Automatic Invoice Collection System — From Scratch (Python)
*Generated on 2025-11-06 18:19*

This document provides a comprehensive guide to building a self‑hosted, Python-based **Automatic Invoice Collection System** (without relying on platforms like Make.com). It's structured as **Prompt → Work it will do → Implementation**, repeated for each section, offering a clear and actionable path to automation.

The system is designed to preserve your original intent: **create Gmail drafts (not auto-send)** for escalating invoice reminders based on the number of days overdue, driven by data in **Google Sheets** (or a database). This approach balances automation with a crucial human review step.

---

## High-Level Summary

- **Goal:** Reduce invoice collection time and free up valuable founder hours by automating approximately 95% of the follow-up process, while maintaining a human element through Gmail **drafts**.
- **Core pieces:** Data source (Google Sheets) → Scheduler/Router (Python) → Draft creation (Gmail API) → Optional review CLI/terminal checklist.
- **Results target:** Implement a 6-stage sequence of reminders (7/14/21/28/35/42 days overdue), progressively firming the tone of the email, with the owner reviewing drafts daily and clicking "Send."
- **Privacy & control:** The system runs on your own machine or server, stores credentials locally, and avoids reliance on third-party automation platforms, ensuring data privacy and control.

---

## Architecture (Overview)

This diagram illustrates the flow of data and actions within the system.

```bash
        ┌──────────────────────────┐
        │ Google Sheets (Invoices) │
        │  - status, due_date,     │
        │    client, amount, etc.  │
        └───────────┬──────────────┘
                    │ read/write via API (using pandas)
                    ▼
           ┌──────────────────┐
           │  Python Scheduler│
           │  (APScheduler)    │
           │  - Runs periodically│
           └───────┬──────────┘
                   │  routes by days overdue
                   ▼
           ┌──────────────────┐
           │ Reminder Router  │
           │  (7/14/21/28/35/42)│
           │  - Selects template│
           │  - Merges data     │
           └───────┬──────────┘
                   │  selects template + merge fields
                   ▼
           ┌──────────────────┐
           │ Gmail API        │
           │  create DRAFTS   │
           │  - Uses OAuth 2.0│
           └──────────────────┘
```

---

# Section 1 — Project Scaffold & Repo

### Prompt
**“Create a clean Python project scaffold for an invoice collections engine with modules for sheets, routing, email, and templates; include tests and a Makefile.”**

### Work it will do
- Creates directories and starter files to ensure the codebase remains organized, modular, and testable.  This structure promotes maintainability and scalability.

### Implementation
```bash
invoice-collector/
├── src/
│   ├── __init__.py
│   ├── config.py         # Configuration settings (API keys, etc.)
│   ├── sheets.py         # Handles Google Sheets interaction
│   ├── router.py         # Routes invoices based on overdue days
│   ├── emailer.py        # Manages Gmail API interaction
│   ├── scheduler.py      # Schedules the invoice collection process
│   ├── models.py         # Defines data structures (Invoice, Client, etc.)
│   └── templates/        # Email templates for different stages
│       ├── stage_07.txt  # Template for 7 days overdue
│       ├── stage_14.txt  # Template for 14 days overdue
│       ├── stage_21.txt  # Template for 21 days overdue
│       ├── stage_28.txt  # Template for 28 days overdue
│       ├── stage_35.txt  # Template for 35 days overdue
│       └── stage_42.txt  # Template for 42 days overdue
├── tests/
│   ├── test_router.py    # Tests for the routing logic
│   └── test_templates.py # Tests for the email templates
├── .env.example      # Example environment variables
├── requirements.txt  # Python dependencies
├── README.md         # Project documentation
└── main.py           # Entry point of the application
```

**requirements.txt**
```bash
google-api-python-client==2.151.0
google-auth==2.35.0
google-auth-oauthlib==1.2.1
pandas==2.2.3
python-dotenv==1.0.1
APScheduler==3.10.4
tabulate==0.9.0
```

**Explanation of dependencies:**

*   `google-api-python-client`:  Official Google API client for Python.
*   `google-auth`: Authentication library for Google APIs.
*   `google-auth-oauthlib`: OAuth 2.0 flow helpers for Google APIs.
*   `pandas`: Data analysis library for working with Google Sheets data.
*   `python-dotenv`: Loads environment variables from a `.env` file.
*   `APScheduler`:  Advanced Python Scheduler for scheduling tasks.
*   `tabulate`:  Library for creating nicely formatted tables (for CLI output).

---

# Section 2 — Environment & Virtualenv

### Prompt
**“Give me the exact shell commands to set up a Python venv, install deps, and run a basic sanity check.”**

### Work it will do
- Sets up an isolated Python virtual environment and verifies that the necessary dependencies are installed correctly. This ensures that the project's dependencies don't conflict with other Python projects on your system.

### Implementation
```bash
python3 -m venv .venv  # Create the virtual environment
source .venv/bin/activate # Activate the virtual environment
pip install --upgrade pip # Upgrade pip to the latest version
pip install -r requirements.txt # Install dependencies from requirements.txt

# Sanity check: Verify that pandas and apscheduler are installed and importable.
python -c "import pandas, apscheduler; print('OK')"
```

**Explanation:**

1.  `python3 -m venv .venv`: Creates a virtual environment in a directory named `.venv`.
2.  `source .venv/bin/activate`: Activates the virtual environment.  Your shell prompt will likely change to indicate that the virtual environment is active.
3.  `pip install --upgrade pip`: Ensures you have the latest version of `pip`, the Python package installer.
4.  `pip install -r requirements.txt`: Installs all the packages listed in the `requirements.txt` file.
5.  `python -c "import pandas, apscheduler; print('OK')"`:  A quick check to confirm that the `pandas` and `apscheduler` libraries are installed correctly and can be imported.  If the command executes without errors and prints "OK", the installation was successful.

---

# Section 3 — Google Cloud + APIs (OAuth)

### Prompt
**“Walk me through creating a Google Cloud project, enabling Sheets + Gmail APIs, and downloading OAuth credentials for a desktop app.”**

### Work it will do
- Creates an OAuth 2.0 client ID in Google Cloud, enables the necessary Google APIs (Sheets and Gmail), and downloads the client credentials file.  This file is essential for authenticating your application with Google's services.

### Implementation

1.  **Create a Google Cloud Project:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Click on the project dropdown at the top and select "New Project."
    *   Enter a project name and click "Create."

2.  **Enable the Google Sheets and Gmail APIs:**
    *   In the Google Cloud Console, navigate to "APIs & Services" → "Library."
    *   Search for "Google Sheets API" and click "Enable."
    *   Search for "Gmail API" and click "Enable."

3.  **Create OAuth 2.0 Credentials:**
    *   In the Google Cloud Console, navigate to "APIs & Services" → "Credentials."
    *   Click "Create Credentials" → "OAuth client ID."
    *   Select "Desktop app" as the application type.
    *   Enter a name for the client (e.g., "Invoice Collector").
    *   Click "Create."
    *   A popup will appear with your client ID and client secret.  Click "Download JSON" to download the `client_secret.json` file.
    *   Place the `client_secret.json` file in the root directory of your project (i.e., the `invoice-collector/` directory).

4.  **First Run and Authorization:**

    The first time you run your script, it will prompt you to authorize the application to access your Google Sheets and Gmail accounts. This involves opening a web browser and logging in to your Google account.  The script will then store the authorization credentials locally (typically in a file named `token.json`).

    **Important Security Note:** Treat the `client_secret.json` and `token.json` files with care. Do not commit them to version control (e.g., Git). Add them to your `.gitignore` file.

```
# Example .gitignore
.venv/
client_secret.json
token.json
```

---

# Section 4 - Google Sheets Interaction (sheets.py)

### Prompt

**"Write a Python module (sheets.py) using the Google Sheets API and the pandas library to read invoice data from a Google Sheet. The function should take the sheet ID and range as input and return a pandas DataFrame. Include error handling for common API issues."**

### Work it will do

- Implements the logic to connect to Google Sheets, authenticate using the OAuth credentials, and read data into a pandas DataFrame for easy manipulation.

### Implementation

```python
# src/sheets.py
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
from google.oauth2.credentials import Credentials

def get_sheets_data(sheet_id, data_range):
    """
    Reads data from a Google Sheet into a pandas DataFrame.

    Args:
        sheet_id (str): The ID of the Google Sheet.
        data_range (str): The range of data to read (e.g., 'Sheet1!A1:G100').

    Returns:
        pandas.DataFrame: A DataFrame containing the data from the sheet, or None on error.
    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    # Load credentials from token.json if it exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    elif os.path.exists('client_secret.json'):
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    else:
        print('Please download your credentials.json file from Google Cloud and place it in the root directory.')
        return None

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=sheet_id, range=data_range).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return None

        df = pd.DataFrame(values[1:], columns=values[0])  # First row as header
        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == '__main__':
    # Example usage (replace with your actual sheet ID and range)
    sheet_id = 'YOUR_SHEET_ID'  # Replace with your Google Sheet ID
    data_range = 'Invoices!A1:G100'  # Replace with your desired range

    invoice_data = get_sheets_data(sheet_id, data_range)

    if invoice_data is not None:
        print(invoice_data.head())  # Print the first few rows of the DataFrame
```

**Explanation:**

1.  **Import necessary libraries:** `pandas`, `googleapiclient`, `google.oauth2`.
2.  **`get_sheets_data(sheet_id, data_range)` function:**
    *   Takes the Google Sheet ID and data range as input.
    *   Authenticates with the Google Sheets API using OAuth 2.0.  It first checks for a `token.json` file (which stores previously authorized credentials). If it doesn't exist, it uses the `client_secret.json` file to initiate the authorization flow.
    *   Builds a `service` object to interact with the Sheets API.
    *   Calls the `sheets.values().get()` method to retrieve data from the specified sheet and range.
    *   Converts the retrieved data into a pandas DataFrame, using the first row as the header.
    *   Includes error handling to catch potential API exceptions.
    *   Saves the credentials to `token.json` for future use.
3.  **`if __name__ == '__main__':` block:**
    *   Provides an example of how to use the `get_sheets_data` function.
    *   **Important:** Replace `'YOUR_SHEET_ID'` and `'Invoices!A1:G100'` with your actual Google Sheet ID and the range containing your invoice data.

---

# Section 5 - Reminder Router (router.py)

### Prompt

**"Create a Python module (router.py) that takes a pandas DataFrame of invoice data and the number of days overdue as input. It should select the appropriate email template based on the overdue days and return a list of dictionaries, where each dictionary contains the client's email, subject, and body (populated with data from the DataFrame)."**

### Work it will do

- Implements the routing logic to select the correct email template based on how overdue an invoice is.  It also merges the invoice data into the template to personalize the email.

### Implementation

