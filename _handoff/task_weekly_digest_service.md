# Task: Weekly Digest Email Service (Backend Logic)

**Worker Model:** qwen2.5-coder:32b-instruct
**Objective:** Implement backend logic for weekly digest email service (calculation, template, API route)

## ⚠️ DOWNSTREAM HARM ESTIMATE
- **If this fails:** Users won't receive weekly summaries, reducing engagement and upgrade conversions
- **Known pitfalls:** 
  - Don't hard-code email content - use templates
  - Don't query database synchronously - use async SQLAlchemy
  - Don't send emails without error handling
- **Timeout:** 300s (file-heavy task)

## 📚 LEARNINGS APPLIED
- [ ] Using async/await for all database queries (SQLAlchemy 2.0 async)
- [ ] Using Pydantic for request/response validation
- [ ] Following existing code patterns from backend/app/api/
- [ ] No absolute paths, no hardcoded secrets

## 🎯 [ACCEPTANCE CRITERIA] (MANDATORY CHECKLIST)

### File 1: backend/app/services/digest.py
- [ ] **Functional:** Create `calculate_digest(user_id: UUID, db: AsyncSession) -> DigestData` function
  - Query job_history for past 7 days for the user
  - Sum drafts_created from all job history records
  - Get total_outstanding_amount from most recent job history record
  - Return DigestData with drafts_count, outstanding_amount, user info
- [ ] **Functional:** Create `send_digest_email(user: User, digest_data: DigestData) -> bool` function
  - Use SendGrid API to send email
  - Use settings.SENDGRID_API_KEY from config
  - Include error handling and logging
  - Return True if sent successfully, False otherwise
- [ ] **Standards:** Use async/await, type hints, docstrings
- [ ] **Standards:** Import SendGrid from sendgrid library (already in dependencies)

### File 2: backend/app/schemas/digest.py
- [ ] **Functional:** Create DigestData Pydantic schema with fields:
  - drafts_count: int
  - outstanding_amount: Decimal
  - user_name: str
  - user_email: str
  - plan: str (for upgrade prompt logic)
- [ ] **Standards:** Use Pydantic v2 syntax, include Config class if needed

### File 3: backend/app/templates/digest_email.html
- [ ] **Functional:** Create HTML email template with:
  - Greeting with user name
  - Summary: "X drafts created this week"
  - Outstanding amount: "$Y total outstanding"
  - Call to action: "Review your Gmail drafts"
  - Conditional upgrade prompt if plan == "free"
- [ ] **Standards:** Use simple HTML (no complex CSS), include plain text fallback

### File 4: backend/app/api/digest.py
- [ ] **Functional:** Create POST /api/digest/send route
  - Protected by DIGEST_CRON_SECRET header (similar to MAKE_WEBHOOK_API_KEY pattern)
  - Query all active users from database
  - For each user, calculate digest and send email
  - Log results (success/failure counts)
  - Return summary response
- [ ] **Standards:** Follow existing API route patterns from backend/app/api/
- [ ] **Standards:** Use async route handler, proper error handling

### Integration
- [ ] **Verification:** Import digest router in backend/app/main.py
- [ ] **Verification:** Add router with prefix "/api/digest"
- [ ] **Syntax:** All files pass Python syntax check (no import errors)

## 📁 CONTEXT FILES TO READ

Before starting, read these files to understand the patterns:
- `backend/app/core/config.py` - Settings class (add SENDGRID_API_KEY if missing)
- `backend/app/models/user.py` - User model
- `backend/app/models/job_history.py` - JobHistory model
- `backend/app/api/webhooks.py` - Example of API key authentication pattern
- `backend/app/api/users.py` - Example of database queries with async

## 🚫 DO NOT

- DO NOT send actual emails (SendGrid will fail without API key) - just implement the logic
- DO NOT use synchronous database queries - use async
- DO NOT hard-code email content - use template file
- DO NOT create new database tables - use existing users and job_history

## ✅ DONE CRITERIA

When you report "Task Complete", the Floor Manager will verify:
1. All 4 files created with correct structure
2. All acceptance criteria checkboxes can be marked [x]
3. Code follows async patterns from existing codebase
4. No syntax errors, no hardcoded secrets

