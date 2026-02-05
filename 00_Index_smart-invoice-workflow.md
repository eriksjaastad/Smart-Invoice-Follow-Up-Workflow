---
tags:
  - map/project
  - p/smart-invoice-workflow
  - type/ai-agent
  - domain/business-automation
  - status/active
created: 2026-01-02
---

# smart-invoice-workflow: Index

This document serves as the central index for the Smart Invoice Workflow project, an automated invoice collection and follow-up system powered by AI. It provides an overview of the project's purpose, key components, and related documentation.

**Project Goal:** To streamline and automate the accounts receivable process, reducing manual effort and improving cash flow.

## Overview

The Smart Invoice Workflow uses a Python-based engine to:

*   Track invoice statuses in a Google Sheet.
*   Automate email correspondence with customers based on invoice age and payment status.
*   Utilize a multi-stage email template system for professional and increasingly urgent communication.
*   Schedule regular outreach to ensure consistent follow-up.

## Key Components

### 1. Automation Engine

The core of the system, responsible for processing invoices, sending emails, and updating the Google Sheet.

*   **`main.py`**: The main script that orchestrates the entire workflow.
*   **`src/invoice_collector/`**: Contains modular business logic, including:
    *   **`sheets.py`**: Interacts with the Google Sheet to read and write invoice data.
    *   **`emailer.py`**: Sends emails using pre-defined templates.
    *   **`scheduler.py`**: Schedules email sending based on invoice due dates and configured intervals.
*   **`src/invoice_collector/templates/`**: Stores multi-stage email templates. Templates are designed for different stages of invoice overdue status (e.g., 7 days, 14 days, 42 days overdue).

### 2. Documentation

Comprehensive documentation covering various aspects of the project.

*   **`Documents/core/Automatic_Invoice_Collection_System_From_Scratch.md`**: A detailed system blueprint outlining the architecture and design of the workflow.
*   **`Documents/guides/`**: Contains guides for:
    *   **Setup**: Instructions on how to configure the system.
    *   **Quickstart**: A brief guide to get the system running quickly.
    *   **First Sale**: Guidance on using the system to collect on the first invoice.
*   **`Documents/reference/`**: Includes:
    *   **Sales Strategy**: Documentation on effective sales strategies for invoice collection.
    *   **Spreadsheet Templates**: Example Google Sheet templates for managing invoice data.

### 3. Infrastructure

Files necessary for deploying and running the system.

*   **`Dockerfile`**: Defines the container environment for easy deployment using Docker.
*   **`requirements.txt`**: Lists all Python dependencies required to run the project.

## Status

**Tags:** #map/project #p/smart-invoice-workflow
**Status:** #status/active
**Type:** #type/ai-agent
**Last Major Update:** January 2026 (Documents Restructured)
**Purpose:** Business automation for accounts receivable

scaffolding_version: 1.0.0
scaffolding_date: 2026-01-27

## Related Documentation

*   [Automation Reliability](patterns/automation-reliability.md) - General automation patterns and best practices.
*   [[queue_processing_guide]] - Information on queue and workflow management.
*   [[deployment_patterns]] - Deployment strategies and patterns for the system.
*   [[sales_strategy]] - Detailed documentation on sales and business strategies related to invoice collection.
*   [README](README) - The project's README file, providing a quick overview and instructions.

## Getting Started

1.  Refer to the `Documents/guides/Setup` guide for initial configuration.
2.  Explore the `Documents/core/Automatic_Invoice_Collection_System_From_Scratch.md` for a deep dive into the system architecture.
3.  Consult the `README.md` file for a quick start.

<!-- LIBRARIAN-INDEX-START -->

### Subdirectories

| Directory | Files | Description |
| :--- | :---: | :--- |
| [Documents/](Documents/README.md) | 2 | *Auto-generated index. Last updated: 2026-01-24* |

### Files

| File | Description |
| :--- | :--- |
| [AGENTS.md](AGENTS.md) | 🎯 Project Overview |
| [BUSINESS IDEA.md](BUSINESS IDEA.md) | Don't beat yourself up about the "Smart Invoice" workflow being on GitHub. Some of the biggest compa... |
| [CLAUDE.md](CLAUDE.md) | AI Collaboration Instructions |
| [DECISIONS.md](DECISIONS.md) | > *Documenting WHY we made decisions, not just WHAT we built.* |
| [Dockerfile](Dockerfile) | No description available. |
| [Documents/README.md](Documents/README.md) | *Auto-generated index. Last updated: 2026-01-24* |
| [Documents/REVIEWS_AND_GOVERNANCE_PROTOCOL.md](Documents/REVIEWS_AND_GOVERNANCE_PROTOCOL.md) | 🛡️ Ecosystem Governance & Review Protocol (v1.2) |
| [Documents/core/Automatic_Invoice_Collection_System_From_Scratch.md](Documents/core/Automatic_Invoice_Collection_System_From_Scratch.md) | Automatic Invoice Collection System — From Scratch (Python) |
| [Documents/core/Smart Invoice Follow-Up Workflow.md](Documents/core/Smart Invoice Follow-Up Workflow.md) | Today’s Client Ready Workflow solves one of the most painful problems every service business faces: |
| [Documents/guides/FIRST_SALE_GUIDE.md](Documents/guides/FIRST_SALE_GUIDE.md) | First Sale Guide for the Smart Invoice Follow-Up System |
| [Documents/guides/QUICK_START.md](Documents/guides/QUICK_START.md) | Quick Start Guide: Invoice Collector |
| [Documents/guides/SETUP.md](Documents/guides/SETUP.md) | Complete setup instructions for the smart-invoice-workflow Python implementation. This guide walks y... |
| [Documents/patterns/code-review-standard.md](Documents/patterns/code-review-standard.md) | Code Review Standardization |
| [Documents/patterns/learning-loop-pattern.md](Documents/patterns/learning-loop-pattern.md) | Learning Loop Pattern |
| [Documents/reference/GOOGLE_SHEET_TEMPLATE.md](Documents/reference/GOOGLE_SHEET_TEMPLATE.md) | Google Sheets Template for Invoice Tracking |
| [Documents/reference/LOCAL_MODEL_LEARNINGS.md](Documents/reference/LOCAL_MODEL_LEARNINGS.md) | Local Model Learnings |
| [Documents/reference/SALES_STRATEGY.md](Documents/reference/SALES_STRATEGY.md) | Sales Strategy Guide for Invoice Collection System |
| [README.md](README.md) | Smart Invoice Workflow |
| [email_autoresponder.json](email_autoresponder.json) | No description available. |
| [main.py](main.py) | No description available. |
| [pyproject.toml](pyproject.toml) | No description available. |
| [requirements.txt](requirements.txt) | No description available. |

<!-- LIBRARIAN-INDEX-END -->