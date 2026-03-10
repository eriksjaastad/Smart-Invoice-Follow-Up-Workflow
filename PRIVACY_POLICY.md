---
tags:
  - p/smart-invoice-workflow
  - type/legal
  - domain/legal
status: "#status/ready-for-review"
created: 2026-02-28
updated: 2026-03-08
---

# Privacy Policy

**Product:** Smart Invoice Workflow  
**Company:** Synth Insight Labs  
**Website:** https://smartinvoiceworkflow.com  
**Effective Date:** March 8, 2026  
**Contact:** admin@synthinsightlabs.com

---

## 1. Summary

Smart Invoice Workflow ("we," "us," or "our") helps freelancers and small businesses automate invoice follow-up using their existing Google Sheet and Gmail. We collect and use data to provide this service. We do not sell your personal information.

---

## 2. Information We Collect

We collect only what is necessary to run the Service:

- **Account data:** Your name, email address, and business name (provided during onboarding); your Auth0 user identifier.
- **Google Sheet identifier:** The Sheet ID you connect. We store only this identifier — we do not store the contents of your spreadsheet. Invoice data (client names, emails, amounts, due dates) lives in your Google Sheet, not our database.
- **Job history and run metadata:** Timestamps of when your daily invoice processing job ran, counts of emails drafted, and error logs for debugging.
- **Payment data:** Billing is handled entirely by Stripe. We store your Stripe customer ID and subscription ID for billing management. We do not store card numbers or payment details.
- **Usage data:** Standard server logs (request timestamps, IP addresses, error traces) for security and reliability.

We do **not** store your Google OAuth tokens, Gmail messages, or the contents of invoices processed on your behalf.

---

## 3. How We Use Information

We use your data to:

- Authenticate you and maintain your account
- Connect to your Google Sheet (via Make.com) to identify invoices due for follow-up
- Create Gmail draft emails in your inbox on your behalf
- Process billing and subscription management via Stripe
- Send operational emails (weekly digest summaries of job results, billing receipts)
- Monitor service reliability and diagnose errors

---

## 4. Service Processors

We use the following third-party services to operate the Service. Each has its own privacy policy governing its use of data:

| Processor | Purpose | Privacy Policy |
|-----------|---------|----------------|
| Make.com | Automation (connects Google Sheets & Gmail OAuth flow) | https://www.make.com/en/privacy-notice |
| Google | Google Sheets API, Gmail API | https://policies.google.com/privacy |
| Auth0 | User authentication | https://www.okta.com/privacy-policy/ |
| Stripe | Payment processing | https://stripe.com/privacy |
| Resend | Transactional email delivery | https://resend.com/legal/privacy-policy |
| Vercel | Application hosting | https://vercel.com/legal/privacy-policy |

---

## 5. Google API Limited Use Disclosure

Smart Invoice Workflow's use and transfer to any other app of information received from Google APIs will adhere to the [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy), including the Limited Use requirements.

Specifically:
- We request access to your Google Sheets data solely to read invoice statuses from the sheet you select, and to your Gmail to create draft emails — no other purpose.
- We do not use your Google user data to serve advertising.
- We do not allow humans to read your Google user data, except when required by law, for security investigation, or with your explicit permission.
- We do not transfer your Google user data to third parties, except as necessary to provide the Service (to Make.com, which processes the OAuth connection on our behalf) or as required by law.

You can revoke Google access at any time from your [Google Account security page](https://myaccount.google.com/permissions).

---

## 6. Data Retention

We retain your account data while your account is active. If you cancel, we may retain data for up to 90 days to allow account recovery, after which it is deleted. You may request earlier deletion by contacting us.

Job history logs are retained for 12 months.

---

## 7. Your Choices and Rights

You can:

- **Update your account information** in your dashboard settings.
- **Disconnect Google** at any time from your [Google Account permissions](https://myaccount.google.com/permissions).
- **Request access, correction, or deletion** of your account data by emailing us.
- **Cancel your subscription** at any time; your data is retained for 90 days after cancellation.

**EU/EEA Users (GDPR):** If you are located in the European Economic Area, you have additional rights under the General Data Protection Regulation (GDPR):

- **Legal basis:** We process your data on the basis of contract performance (to provide the Service you signed up for) and legitimate interests (security, fraud prevention).
- **Data Subject Rights:** Right of access, rectification, erasure, restriction, data portability, and objection. You also have the right to lodge a complaint with your local supervisory authority.
- **Data Transfers:** Your data may be processed in the United States. Where required, we rely on Standard Contractual Clauses or other approved transfer mechanisms.

To exercise your GDPR rights or appoint a representative, contact us at admin@synthinsightlabs.com.

---

## 8. Security

We implement reasonable administrative and technical safeguards, including encrypted connections (HTTPS), access controls, and secure credential storage via Doppler. No internet transmission is 100% secure. We will notify you of a data breach as required by applicable law.

---

## 9. Cookies

We use session cookies necessary for authentication (set by Auth0). We do not use third-party tracking or advertising cookies.

---

## 10. Children's Privacy

The Service is not directed to children under 13. We do not knowingly collect data from children under 13. If we learn we have collected such data, we will delete it.

---

## 11. Changes to This Policy

We may update this Policy. We will revise the "Updated" date at the top and, for material changes, provide notice via email or the dashboard. Continued use of the Service after changes constitutes acceptance.

---

## 12. Contact

Privacy questions or data requests: **admin@synthinsightlabs.com**
