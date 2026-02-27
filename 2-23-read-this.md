Quick Start for Tomorrow Morning
Before you open the project, jot down these 3 things tonight (or on the drive in):

1. The "Release Contract" questions for Smart Invoice:

What does fully shipped look like? (e.g., "An invoice comes in → gets parsed → draft sent to client → client approves → payment tracked")
What must never happen? (e.g., "Wrong amount on an invoice", "Email sent to wrong person", "Duplicate charge")
What's explicitly out of scope for this release?
2. Your Scenario seeds (you already have one!):

✅ S-01: Invoice received → draft email generated correctly (you proved this tonight)
❓ S-02: What happens when the invoice has a typo / missing field?
❓ S-03: What happens when the make.com webhook fails?
❓ S-04: What happens when the client doesn't respond?
3. The evidence question:

After make.com runs — where do you look to know it worked? A log? An email thread? A dashboard? That "where you look" becomes your EVIDENCE.md.
The Make.com Angle
One thing worth noting for Smart Invoice specifically — make.com scenarios are actually perfect for the StrongDM model. Each make.com automation run already produces logs with pass/fail per step. That's your evidence bundle with almost no extra work.

When you sit down tomorrow, the move is:

Open the PRD (or write a quick one if it's scattered)
Add the Release Contract section at the bottom
Write SCENARIOS.md — 5–10 scenarios based on what you know make.com does
Map each scenario to "where do I look to confirm it worked"