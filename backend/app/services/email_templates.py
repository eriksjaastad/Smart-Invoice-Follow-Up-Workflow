"""
Escalation email templates.

6 distinct templates implementing the PRD's tone escalation:
  Stage 1 (7 days):  Friendly check-in
  Stage 2 (14 days): Direct follow-up
  Stage 3 (21 days): Urgent
  Stage 4 (28 days): Firm + call suggestion
  Stage 5 (35 days): Final before escalation
  Stage 6 (42 days): Last notice — mentions collections/legal

Template variables:
  sender_name, business_name, client_name, invoice_number, amount, due_date, days_overdue
"""
from app.services.escalation import STAGES

# Map stage days → 1-based stage number for template selection
_STAGE_INDEX = {days: idx + 1 for idx, days in enumerate(STAGES)}


def get_stage_number(stage_days: int) -> int:
    """Convert stage days (7, 14, ...) to stage number (1, 2, ...)."""
    return _STAGE_INDEX.get(stage_days, 1)


def get_subject(stage_days: int, invoice_number: str, business_name: str) -> str:
    """Generate email subject line based on escalation stage."""
    n = get_stage_number(stage_days)
    subjects = {
        1: f"Friendly reminder: Invoice {invoice_number} from {business_name}",
        2: f"Following up: Invoice {invoice_number} from {business_name}",
        3: f"Urgent: Invoice {invoice_number} is now 3 weeks overdue",
        4: f"Action needed: Invoice {invoice_number} — {business_name}",
        5: f"Final reminder: Invoice {invoice_number} before escalation",
        6: f"Last notice: Invoice {invoice_number} — immediate action required",
    }
    return subjects.get(n, subjects[1])


def get_body_html(
    stage_days: int,
    sender_name: str,
    business_name: str,
    client_name: str,
    invoice_number: str,
    amount: str,
    due_date: str,
    days_overdue: int,
) -> str:
    """
    Generate HTML email body for the given escalation stage.

    Returns a complete HTML email body string.
    """
    n = get_stage_number(stage_days)
    ctx = dict(
        sender_name=sender_name,
        business_name=business_name,
        client_name=client_name,
        invoice_number=invoice_number,
        amount=amount,
        due_date=due_date,
        days_overdue=days_overdue,
    )
    templates = {
        1: _stage_1,
        2: _stage_2,
        3: _stage_3,
        4: _stage_4,
        5: _stage_5,
        6: _stage_6,
    }
    fn = templates.get(n, _stage_1)
    return fn(**ctx)


def _wrap(body_content: str) -> str:
    """Wrap body content in minimal HTML email structure."""
    return f"""\
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
{body_content}
</body>
</html>"""


def _stage_1(
    sender_name: str,
    business_name: str,
    client_name: str,
    invoice_number: str,
    amount: str,
    due_date: str,
    days_overdue: int,
) -> str:
    """Stage 1: Friendly check-in — casual, assumes oversight."""
    return _wrap(f"""\
<p>Hi {client_name},</p>

<p>Hope you're doing well! I wanted to quickly check in about invoice <strong>{invoice_number}</strong> for <strong>{amount}</strong> that was due on {due_date}.</p>

<p>It's been about {days_overdue} days since the due date, so I figured I'd reach out in case it slipped through the cracks. Totally understandable if so!</p>

<p>If you've already sent payment, please disregard this message. Otherwise, could you let me know when I can expect it?</p>

<p>Thanks so much,<br>
{sender_name}<br>
{business_name}</p>""")


def _stage_2(
    sender_name: str,
    business_name: str,
    client_name: str,
    invoice_number: str,
    amount: str,
    due_date: str,
    days_overdue: int,
) -> str:
    """Stage 2: Direct follow-up — polite but clear."""
    return _wrap(f"""\
<p>Hi {client_name},</p>

<p>I'm following up on invoice <strong>{invoice_number}</strong> for <strong>{amount}</strong>, which was due on {due_date} — now {days_overdue} days ago.</p>

<p>I haven't received payment or heard back yet, so I wanted to make sure this is on your radar. If there's an issue with the invoice or payment timeline, I'm happy to discuss.</p>

<p>Could you please provide an update on the expected payment date?</p>

<p>Best regards,<br>
{sender_name}<br>
{business_name}</p>""")


def _stage_3(
    sender_name: str,
    business_name: str,
    client_name: str,
    invoice_number: str,
    amount: str,
    due_date: str,
    days_overdue: int,
) -> str:
    """Stage 3: Urgent — emphasizes 3 weeks overdue."""
    return _wrap(f"""\
<p>Hi {client_name},</p>

<p>This is an urgent follow-up regarding invoice <strong>{invoice_number}</strong> for <strong>{amount}</strong>. This invoice was due on {due_date} and is now <strong>{days_overdue} days overdue</strong>.</p>

<p>I've reached out previously without a response. I'd really appreciate hearing back so we can resolve this promptly.</p>

<p>If there are any issues preventing payment, please let me know and we can work something out.</p>

<p>Thank you,<br>
{sender_name}<br>
{business_name}</p>""")


def _stage_4(
    sender_name: str,
    business_name: str,
    client_name: str,
    invoice_number: str,
    amount: str,
    due_date: str,
    days_overdue: int,
) -> str:
    """Stage 4: Firm + call suggestion — requests direct contact."""
    return _wrap(f"""\
<p>Hi {client_name},</p>

<p>I need to bring your attention to invoice <strong>{invoice_number}</strong> for <strong>{amount}</strong>, now <strong>{days_overdue} days past due</strong> (originally due {due_date}).</p>

<p>This is my fourth attempt to reach you about this outstanding balance. I'd like to resolve this amicably and would suggest we schedule a quick call to discuss.</p>

<p>Please reply to this email or reach out at your earliest convenience so we can find a resolution.</p>

<p>Regards,<br>
{sender_name}<br>
{business_name}</p>""")


def _stage_5(
    sender_name: str,
    business_name: str,
    client_name: str,
    invoice_number: str,
    amount: str,
    due_date: str,
    days_overdue: int,
) -> str:
    """Stage 5: Final before escalation — warns of next steps."""
    return _wrap(f"""\
<p>Dear {client_name},</p>

<p>This is a final reminder regarding invoice <strong>{invoice_number}</strong> for <strong>{amount}</strong>, which has been outstanding for <strong>{days_overdue} days</strong> (due date: {due_date}).</p>

<p>Despite multiple attempts to reach you, I have not received payment or a response. If payment is not received or arrangements made within the next 7 days, I will need to consider escalating this matter.</p>

<p>I strongly encourage you to reach out so we can resolve this before any further steps are necessary.</p>

<p>Sincerely,<br>
{sender_name}<br>
{business_name}</p>""")


def _stage_6(
    sender_name: str,
    business_name: str,
    client_name: str,
    invoice_number: str,
    amount: str,
    due_date: str,
    days_overdue: int,
) -> str:
    """Stage 6: Last notice — mentions collections/legal."""
    return _wrap(f"""\
<p>Dear {client_name},</p>

<p><strong>LAST NOTICE</strong> — Invoice <strong>{invoice_number}</strong> for <strong>{amount}</strong> is now <strong>{days_overdue} days past due</strong> (original due date: {due_date}).</p>

<p>This is the final communication I will send before referring this matter to a collections agency or seeking legal counsel. I have made every effort to resolve this amicably over the past several weeks.</p>

<p>To avoid further action, please arrange payment immediately or contact me to discuss a payment plan.</p>

<p>This matter requires your immediate attention.</p>

<p>Regards,<br>
{sender_name}<br>
{business_name}</p>""")
