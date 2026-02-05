# Quick Start Guide: Invoice Collector

Get the Invoice Collector running in **under 10 minutes** and automate your overdue invoice reminders.

## Prerequisites Checklist

Before you begin, ensure you have the following:

- [x] Python 3.11+ installed.  Verify with `python3 --version`.
- [x] A Gmail account.
- [x] A Google Sheet to store your invoice data.
- [x] A Google Cloud project.
- [x] Doppler CLI installed and configured (optional, but recommended for secrets management).  See [Doppler Secrets Management](Documents/reference/DOPPLER_SECRETS_MANAGEMENT.md) for details.

## 5-Minute Setup

### Step 1: Installation (1 min)

1.  **Clone or download the repository:**

    ```bash
    git clone <repository_url>  # Replace <repository_url> with the actual URL
    cd smart-invoice-workflow
    ```

2.  **Create a virtual environment:**

    ```bash
    python3 -m venv .venv
    ```

3.  **Activate the virtual environment:**

    ```bash
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate  # Windows
    ```

4.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

### Step 2: Google Cloud Setup (3 min)

1.  **Go to the [Google Cloud Console](https://console.cloud.google.com/).**

2.  **Create a new project:**  Name it "invoice-collector" or something similar.

3.  **Enable APIs:**
    *   Search for and enable the **Google Sheets API**.
    *   Search for and enable the **Gmail API**.

4.  **Create OAuth 2.0 credentials:**
    *   Go to "APIs & Services" -> "Credentials".
    *   Click "+ CREATE CREDENTIALS" -> "OAuth client ID".
    *   Application type: "Desktop app".
    *   Name: "Invoice Collector".
    *   Click "CREATE".
    *   Download the generated `client_secret.json` file.
    *   Save the `client_secret.json` file to the root directory of your project.

### Step 3: Configuration (1 min)

1.  **Copy the example environment file:**

    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file:**

    ```
    SPREADSHEET_ID=<your_spreadsheet_id>
    GMAIL_ADDRESS=<your_gmail_address>
    DRY_RUN=true  # Set to 'false' to send actual emails
    ```

    *   **`SPREADSHEET_ID`:**  The ID of your Google Sheet (see Step 4).
    *   **`GMAIL_ADDRESS`:**  The Gmail address you'll be sending emails from.
    *   **`DRY_RUN`:**  Set to `true` to prevent actual emails from being sent during testing.  Change to `false` to send live emails.

    **Using Doppler (Recommended):** If you're using Doppler for secrets management, you can skip creating a `.env` file and instead configure these variables within your Doppler project.  Refer to [Doppler Secrets Management](Documents/reference/DOPPLER_SECRETS_MANAGEMENT.md) for more information.  If using Doppler, you will run the application with `doppler run -- python main.py`.

### Step 4: Create Google Sheet (2 min)

1.  **Create a new Google Sheet.**

2.  **Add the following headers to the first row:**

    ```
    invoice_id | client_name | client_email | amount | currency | due_date | sent_date | status | notes | last_stage_sent | last_sent_at
    ```

    *   **`invoice_id`:** Unique identifier for the invoice (e.g., INV-001).
    *   **`client_name`:** Name of the client.
    *   **`client_email`:** Email address of the client.
    *   **`amount`:** Invoice amount.
    *   **`currency`:** Currency code (e.g., USD, EUR).
    *   **`due_date`:** Invoice due date (YYYY-MM-DD).
    *   **`sent_date`:** Date the invoice was originally sent (YYYY-MM-DD).
    *   **`status`:** Invoice status (e.g., Overdue, Paid, Sent).  The script will only process invoices with the status "Overdue".
    *   **`notes`:** Any relevant notes.
    *   **`last_stage_sent`:**  The last escalation stage sent (e.g., 7, 14, 21).  Leave blank initially.
    *   **`last_sent_at`:**  Timestamp of the last reminder sent (YYYY-MM-DD HH:MM:SS). Leave blank initially.

3.  **Add a test invoice:**

    ```
    INV-001 | John Smith | john@example.com | 2500 | USD | 2024-01-01 | 2023-12-15 | Overdue | Test |  |
    ```

    *   Make sure the `due_date` is in the past to trigger the overdue logic.

4.  **Get the spreadsheet ID:**  The spreadsheet ID is part of the URL of your Google Sheet.  It's the long string of characters between `/d/` and `/edit`.  For example, in the URL `https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit#gid=0`, the spreadsheet ID is `YOUR_SPREADSHEET_ID`.  Paste this ID into the `SPREADSHEET_ID` variable in your `.env` file.

### Step 5: First Run (1 min)

1.  **Run the script in dry-run mode:**

    ```bash
    doppler run -- python main.py --dry-run  # If using Doppler
    # OR
    python main.py --dry-run # If using .env
    ```

2.  **Authenticate with Google:**  Your browser will open and prompt you to authenticate with your Google account.  Grant the application the necessary permissions to access your Gmail and Google Sheets.

3.  **Review the output:**  The script will print information about the invoices it found and the drafts it *would* create.  Since `DRY_RUN` is set to `true`, no actual emails will be sent.

4.  **Verify everything works:**  Check the output for any errors.  Make sure the script is correctly identifying your overdue invoice and creating the appropriate draft.

### Step 6: Go Live

1.  **Edit the `.env` file:**

    ```
    DRY_RUN=false
    ```

2.  **Run the script:**

    ```bash
    doppler run -- python main.py  # If using Doppler
    # OR
    python main.py # If using .env
    ```

3.  **Check Gmail:**  The script will create drafts in your Gmail account.

4.  **Review and send:**  Carefully review each draft before sending it.  You can personalize the drafts if needed.

## Daily Usage

1.  **Run the script once per day:**  Schedule the script to run automatically using a cron job or a similar scheduler.

    ```bash
    doppler run -- python main.py  # If using Doppler
    # OR
    python main.py # If using .env
    ```

2.  **Review drafts in Gmail:**  Check your Gmail drafts folder for new drafts created by the script.

3.  **Click Send:**  Review each draft and click "Send" to send the reminder email.  Consider personalizing the emails for a more human touch.

## Common Commands

```bash
# Dry run (preview only)
doppler run -- python main.py --dry-run

# Verbose logging
doppler run -- python main.py --verbose

# Show help message
python main.py --help
```

## What Happens Daily

1.  The system reads your Google Sheet and identifies invoices with a "Status" of "Overdue".
2.  It calculates the number of days overdue for each invoice.
3.  Based on the days overdue, it determines the appropriate reminder stage (7, 14, 21, 28, 35, or 42 days).
4.  It creates a Gmail draft using a pre-defined template for the corresponding reminder stage.
5.  It updates the "last_stage_sent" and "last_sent_at" columns in your Google Sheet to track the reminders that have been sent.
6.  You review the drafts in Gmail and send them manually.

## Escalation Timeline

| Days Overdue | What Gets Sent             |
|--------------|--------------------------|
| 7            | Friendly check-in          |
| 14           | Direct follow-up         |
| 21           | Urgent reminder            |
| 28           | Firm tone + call suggestion |
| 35           | Final warning              |
| 42           | Collections notice         |

## Troubleshooting

*   **"client_secret.json not found"**:
    *   Ensure you downloaded the `client_secret.json` file from the Google Cloud Console and saved it to the project root directory.
*   **"No invoices found"**:
    *   Verify that the `SPREADSHEET_ID` in your `.env` file is correct.
    *   Make sure that the sheet name is correct (the default is usually "Sheet1").
    *   Ensure that you have invoices with the "Status" set to "Overdue".
*   **"403 permissions error"**:
    *   Double-check that you have enabled the Gmail API and Google Sheets API in the Google Cloud Console.
    *   Make sure you have granted the application the necessary permissions when authenticating with Google.
*   **"ModuleNotFoundError: No module named 'google.auth'"**:
    *   Make sure you have activated your virtual environment and installed the required packages using `pip install -r requirements.txt`.

**Want more details?**

See [SETUP.md](SETUP.md) for a complete guide with detailed explanations and advanced configuration options.

---

**That's it! You're up and running. 🚀**

The system automates 95% of the work - you just review and send.

## Related Documentation

- [Doppler Secrets Management](Documents/reference/DOPPLER_SECRETS_MANAGEMENT.md) - Secrets management with Doppler
- [[PROJECT_KICKOFF_GUIDE]] - Project setup best practices
- [Automation Reliability](patterns/automation-reliability.md) - Common automation patterns
- [[error_handling_patterns]] - Strategies for robust error handling
- [[queue_processing_guide]] - Managing workflows with queues
- [[case_studies]] - Real-world examples and use cases
- [Safety Systems](patterns/safety-systems.md) - Security considerations and best practices
- [[testing_strategy]] - Testing and quality assurance strategies
- [README](README) - Smart Invoice Workflow project overview
