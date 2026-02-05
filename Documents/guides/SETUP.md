# Setup Guide - Smart Invoice Workflow

Complete setup instructions for the smart-invoice-workflow Python implementation. This guide walks you through the process of setting up the application, configuring Google Cloud and Google Sheets, and running the workflow for the first time.

## Table of Contents

1.  [Prerequisites](#prerequisites)
2.  [Installation](#installation)
    *   [Option 1: Using pip (Standard)](#option-1-using-pip-standard)
    *   [Option 2: Using uv (Faster)](#option-2-using-uv-faster)
3.  [Google Cloud Setup](#google-cloud-setup)
    *   [1. Create a Google Cloud Project](#1-create-a-google-cloud-project)
    *   [2. Enable Required APIs](#2-enable-required-apis)
    *   [3. Create OAuth Credentials](#3-create-oauth-credentials)
4.  [Google Sheets Setup](#google-sheets-setup)
    *   [1. Create Your Invoice Tracking Sheet](#1-create-your-invoice-tracking-sheet)
    *   [2. Column Descriptions](#2-column-descriptions)
    *   [3. Example Data](#3-example-data)
    *   [4. Get the Spreadsheet ID](#4-get-the-spreadsheet-id)
5.  [Configuration](#configuration)
    *   [Environment Variables](#environment-variables)
    *   [Doppler Setup (Recommended)](#doppler-setup-recommended)
    *   [Manual Configuration (Alternative)](#manual-configuration-alternative)
6.  [First Run](#first-run)
7.  [Deployment](#deployment)
8.  [Troubleshooting](#troubleshooting)

---

## Prerequisites

-   **Python 3.11 or higher:** Ensure you have Python 3.11 or a later version installed. You can check your Python version by running `python3 --version` in your terminal.
-   **Google Account:** You'll need a Google Account with access to Gmail and Google Sheets.
-   **Google Cloud Project:** A Google Cloud Project is required to access Google APIs.
-   **pip** or **uv:** Package managers for installing Python dependencies. `uv` is significantly faster.
-   **Doppler (Recommended):** For managing secrets and environment variables.  Sign up for a free account at [Doppler](https://doppler.com/).
-   **Text Editor or IDE:**  A text editor (like VS Code, Sublime Text, or Atom) or an IDE (like PyCharm) will be helpful for editing configuration files.

---

## Installation

### Option 1: Using pip (Standard)

```bash
# Clone or download this repository
git clone <repository_url> # Replace <repository_url> with the actual repository URL
cd smart-invoice-workflow

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate  # On Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Option 2: Using uv (Faster)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate  # On Windows
uv pip install -r requirements.txt
```

---

## Google Cloud Setup

### 1. Create a Google Cloud Project

1.  Go to [Google Cloud Console](https://console.cloud.google.com/)
2.  Click **"Create Project"**
3.  Name it something like `invoice-collector`
4.  Click **"Create"**
5.  **Note the Project ID:** You'll need this later.  It's a unique identifier for your project.

### 2. Enable Required APIs

1.  In your project, go to **"APIs & Services"** → **"Library"**
2.  Search for and enable:
    -   **Google Sheets API**
    -   **Gmail API**

### 3. Create OAuth Credentials

1.  Go to **"APIs & Services"** → **"Credentials"**
2.  Click **"Create Credentials"** → **"OAuth client ID"**
3.  If prompted, configure the OAuth consent screen:
    -   User Type: **External** (unless you have a workspace)
    -   App name: `Invoice Collector`
    -   User support email: Your email address
    -   Developer contact: Your email address
    -   Scopes: Add the following scopes (use the "+ Add Scopes" button):
        -   `https://www.googleapis.com/auth/gmail.compose` (Send emails)
        -   `https://www.googleapis.com/auth/spreadsheets` (Read and write to Google Sheets)
    -   Test users: Add your Gmail address
4.  Create credentials:
    -   Application type: **Desktop app**
    -   Name: `Invoice Collector Desktop`
5.  Click **"Create"**
6.  Click **"Download JSON"**
7.  **Rename the downloaded file to `client_secret.json`**
8.  **Move it to the project root directory** (same folder as `main.py`)

⚠️ **IMPORTANT**: Never commit `client_secret.json` to git. It's already in `.gitignore`. This file contains sensitive information that should be kept secret.

---

## Google Sheets Setup

### 1. Create Your Invoice Tracking Sheet

Create a new Google Sheet with these **exact column headers** in row 1:

| invoice_id | client_name | client_email | amount | currency | due_date   | sent_date  | status    | notes | last_stage_sent | last_sent_at |
| :---------- | :---------- | :----------- | :----- | :------- | :--------- | :--------- | :-------- | :---- | :---------------- | :------------- |
|             |             |              |        |          |            |            |           |       |                   |                |

### 2. Column Descriptions

-   **invoice_id**: Unique identifier for the invoice (e.g., `INV-001`, `2025-001`).  Must be unique for each invoice.
-   **client_name**: Client's full name.
-   **client_email**: Email address where reminders should be sent.
-   **amount**: Invoice amount (numbers only, no currency symbols or commas).
-   **currency**: Currency code (`USD`, `EUR`, `GBP`, etc.).  Must be a valid ISO 4217 currency code.
-   **due_date**: Due date in `MM/DD/YYYY` or `YYYY-MM-DD` format.
-   **sent_date**: Date the invoice was sent, in `MM/DD/YYYY` or `YYYY-MM-DD` format.
-   **status**: Current status of the invoice. Use `Overdue` to trigger reminders. Other possible values: `Paid`, `Sent`, `Draft`.
-   **notes**: Optional notes about the invoice.
-   **last_stage_sent**:  Automatically populated by the system.  Indicates the last reminder stage sent.  Leave blank.
-   **last_sent_at**: Automatically populated by the system.  Indicates the timestamp of the last reminder sent. Leave blank.

### 3. Example Data

Here's a sample row to test with:

| invoice_id | client_name | client_email    | amount | currency | due_date   | sent_date  | status    | notes       | last_stage_sent | last_sent_at |
| :---------- | :---------- | :-------------- | :----- | :------- | :--------- | :--------- | :-------- | :---------- | :---------------- | :------------- |
| INV-001     | John Smith  | john@example.com | 2500   | USD      | 01/15/2025 | 01/01/2025 | Overdue   | Project X   |                   |                |

### 4. Get the Spreadsheet ID

The Spreadsheet ID is a long string of characters in the URL of your Google Sheet.  For example, if your Google Sheet URL is `https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit#gid=0`, then `YOUR_SPREADSHEET_ID` is the Spreadsheet ID.  You'll need this in the next step.

---

## Configuration

The application requires several configuration parameters, including the Spreadsheet ID, Google Cloud Project ID, and other settings.  We recommend using Doppler to manage these as environment variables.

### Environment Variables

The following environment variables need to be set:

-   `SPREADSHEET_ID`: The ID of your Google Sheet (see step 4 above).
-   `PROJECT_ID`: Your Google Cloud Project ID.
-   `CLIENT_SECRET_PATH`: The path to your `client_secret.json` file (should be `./client_secret.json` if you followed the instructions).
-   `APPLICATION_NAME`: A name for your application (e.g., "Invoice Collector").
-   `REMINDER_STAGES`: A comma-separated list of reminder stages (e.g., "1_week,3_days,1_day").  These correspond to the email templates.
-   `EMAIL_SUBJECT`: The subject of the reminder emails.
-   `SENDER_EMAIL`: The email address that will be used to send the reminder emails. This must be an email address associated with the Google account used to create the OAuth credentials.

### Doppler Setup (Recommended)

1.  **Install the Doppler CLI:** Follow the instructions on the [Doppler website](https://docs.doppler.com/docs/install-cli) to install the Doppler CLI.
2.  **Login to Doppler:** Run `doppler login` in your terminal and follow the prompts.
3.  **Create a Doppler Project:**  If you don't already have one, create a new Doppler project.
4.  **Create a Doppler Environment:** Create a development environment (e.g., "dev").
5.  **Set the Environment Variables:** Use the Doppler CLI to set the environment variables:

    ```bash
    doppler secrets set SPREADSHEET_ID=<your_spreadsheet_id>
    doppler secrets set PROJECT_ID=<your_project_id>
    doppler secrets set CLIENT_SECRET_PATH=./client_secret.json
    doppler secrets set APPLICATION_NAME="Invoice Collector"
    doppler secrets set REMINDER_STAGES="1_week,3_days,1_day"
    doppler secrets set EMAIL_SUBJECT="Invoice Reminder"
    doppler secrets set SENDER_EMAIL="your_email@gmail.com" # Replace with your email
    ```

    Replace `<your_spreadsheet_id>` and `<your_project_id>` with your actual values.

6.  **Run the application with Doppler:** Use `doppler run -- python main.py` to run your application with the environment variables loaded from Doppler.

### Manual Configuration (Alternative)

If you don't want to use Doppler, you can set the environment variables manually.  This is generally not recommended for production environments.

1.  **Create a `.env` file:** In the project root directory, create a file named `.env`.
2.  **Add the environment variables:** Add the environment variables to the `.env` file, one per line:

    ```
    SPREADSHEET_ID=<your_spreadsheet_id>
    PROJECT_ID=<your_project_id>
    CLIENT_SECRET_PATH=./client_secret.json
    APPLICATION_NAME="Invoice Collector"
    REMINDER_STAGES="1_week,3_days,1_day"
    EMAIL_SUBJECT="Invoice Reminder"
    SENDER_EMAIL="your_email@gmail.com"
    ```

    Replace `<your_spreadsheet_id>` and `<your_project_id>` with your actual values.

3.  **Load the environment variables:** You'll need to load the environment variables into your application.  You can use a library like `python-dotenv` for this.  Make sure to install it: `pip install python-dotenv`.  Then, in your `main.py` file, add the following lines at the beginning:

    ```python
    from dotenv import load_dotenv
    load_dotenv()
    ```

---

## First Run

After completing the setup, you can run the application for the first time.

1.  **Activate your virtual environment:** If you haven't already, activate your virtual environment:

    ```bash
    source .venv/bin/activate  # On Linux/macOS
    # .venv\Scripts\activate  # On Windows
    ```

2.  **Run the application:**

    -   **If using Doppler:** `doppler run -- python main.py`
    -   **If using manual configuration:** `python main.py`

3.  **Authorize the application:** The first time you run the application, it will prompt you to authorize it to access your Google Sheets and Gmail account.  Follow the instructions in the terminal to complete the authorization process.  This will involve opening a web browser and logging into your Google account.

4.  **Check the results:** After the application runs, check your Google Sheet to see if the `last_stage_sent` and `last_sent_at` columns have been updated.  Also, check your Gmail account to see if any reminder emails have been sent.

---

## Deployment

Instructions for deploying the application to a production environment will be added in a future update.  Consider using platforms like Google Cloud Functions, AWS Lambda, or Heroku.

---

## Troubleshooting

-   **"ModuleNotFoundError: No module named 'googleapiclient'"**: Make sure you have installed the required dependencies using `pip install -r requirements.txt` or `uv pip install -r requirements.txt`.
-   **"Invalid Credentials"**: Double-check that your `client_secret.json` file is in the correct location and that you have enabled the required APIs in your Google Cloud Project.  Also, make sure that the email address you are using to authorize the application is the same email address that you added as a test user in the OAuth consent screen.
-   **"Spreadsheet not found"**: Verify that the `SPREADSHEET_ID` environment variable is set correctly and that the Google Sheet exists.
-   **Emails not being sent**: Ensure that the `SENDER_EMAIL` is correctly configured and that the Gmail API is enabled. Also, check your spam folder.
-   **Permissions issues**: Ensure the correct scopes are enabled in the Google Cloud Console for your project.
-   **Rate limiting**: If you are sending a large number of emails, you may encounter rate limiting from Gmail. Consider implementing a retry mechanism or using a service like SendGrid or Mailgun for sending emails.

If you encounter any other issues, please consult the project's README file or open an issue on the project's GitHub repository.
