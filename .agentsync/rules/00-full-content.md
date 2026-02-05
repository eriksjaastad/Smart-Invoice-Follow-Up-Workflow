---
targets: ["*"]
---

# AGENTS.md - Source of Truth for AI Agents in Smart Invoice Workflow

## 🎯 Project Overview

This document serves as the central repository for defining and documenting the AI agents used within the Smart Invoice Workflow project. It outlines their roles, responsibilities, capabilities, and constraints.  This ensures consistency and clarity across the project and facilitates collaboration.

{project_description}

## 🛠 Tech Stack

- Language: {language}
- Frameworks: {frameworks}
- AI Strategy: {ai_strategy}

## 🤖 Agent Definitions

This section defines the AI agents used in the Smart Invoice Workflow.  Each agent definition should include:

*   **Name:** A descriptive name for the agent.
*   **Role:** The agent's primary function within the workflow.
*   **Responsibilities:** Specific tasks the agent is responsible for.
*   **Capabilities:** The skills and tools the agent possesses.
*   **Constraints:** Limitations or restrictions on the agent's actions.
*   **Communication Protocol:** How the agent interacts with other agents and systems.
*   **State Management:** How the agent maintains its state and context.

### Example Agent Definition: Invoice Data Extractor

*   **Name:** Invoice Data Extractor
*   **Role:** Extracts key data fields from invoice documents.
*   **Responsibilities:**
    *   Identify and extract data fields such as invoice number, date, vendor, total amount, line items, etc.
    *   Validate extracted data against predefined rules and formats.
    *   Handle different invoice formats and layouts.
*   **Capabilities:**
    *   Optical Character Recognition (OCR)
    *   Natural Language Processing (NLP)
    *   Regular expressions
    *   Data validation and cleansing
*   **Constraints:**
    *   Limited accuracy on low-quality or handwritten invoices.
    *   May require human review for complex or ambiguous invoices.
*   **Communication Protocol:** Receives invoice documents as input and outputs structured data in JSON format.
*   **State Management:** Maintains a session context for each invoice being processed.

### [Add Agent Definitions Here]

## 📋 Definition of Done (DoD)

- [ ] Code is documented with type hints.
- [ ] Technical changes are logged to `project-tracker/data/WARDEN_LOG.yaml`.
- [ ] `00_Index_*.md` is updated with recent activity.
- [ ] Code validated (no hardcoded paths, no secrets exposed).
- [ ] Code review completed (if significant architectural changes).
- [ ] [Project-specific DoD item]

## 🚀 Execution Commands

- Environment: `{venv_activation}`
- Run: `{run_command}`
- Test: `{test_command}`

## ⚠️ Critical Constraints

- NEVER hard-code API keys, secrets, or credentials in script files. Use `.env` and `os.getenv()`.
- NEVER use absolute paths (e.g., machine-specific paths). ALWAYS use relative paths or `PROJECT_ROOT` env var.
- ALWAYS run validation before considering work complete: `python "./scripts/validate_project.py" [project-name]`
- {constraint_1}
- {constraint_2}

**Code Review Standards:** See `./REVIEWS_AND_GOVERNANCE_PROTOCOL.md` for full review process.

## 📖 Reference Links

- `00_Index_*.md`
- [[Project Philosophy]]
