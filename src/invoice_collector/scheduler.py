"""
Main scheduler/orchestrator for the invoice collection system

Coordinates the entire workflow:
1. Read overdue invoices from Google Sheets
2. Calculate which stage each invoice should be at
3. Create Gmail drafts for invoices that need reminders
4. Write back tracking data to Google Sheets
"""
import logging
from datetime import date
from typing import List
from tabulate import tabulate

from .config import settings
from .models import Invoice, DraftCreated
from .sheets import read_invoices, write_back_invoices
from .router import days_overdue, stage_for, should_send
from .emailer import create_draft_from_template, template_path_for, render_template

# Set up logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_daily() -> List[DraftCreated]:
    """
    Main daily job that processes all overdue invoices

    Workflow:
    1. Load all invoices from Google Sheets
    2. Filter to only "Overdue" status invoices
    3. For each overdue invoice:
       - Calculate days overdue
       - Determine which stage reminder to send
       - Check if we should send (not already sent today, higher stage)
       - Create Gmail draft with appropriate template
       - Track what was sent
    4. Write back last_stage_sent and last_sent_at to Google Sheets

    Returns:
        List of DraftCreated objects representing drafts that were created
    """
    today = date.today()
    logger.info(f"Starting daily invoice collection run for {today}")

    # Validate configuration
    errors = settings.validate()
    if errors:
        logger.error(f"Configuration errors: {errors}")
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    # Check business hours
    if not settings.is_within_business_hours():
        logger.warning(
            f"Outside business hours (configured: {settings.WINDOW_START}:00-{settings.WINDOW_END}:00). "
            "Run will proceed but you may want to schedule during business hours."
        )

    # Load invoices
    logger.info("Loading invoices from Google Sheets...")
    try:
        all_invoices = read_invoices()
        logger.info(f"Loaded {len(all_invoices)} total invoices")
    except Exception as e:
        logger.error(f"Failed to read invoices: {e}")
        raise

    # Filter to overdue invoices only
    overdue_invoices = [inv for inv in all_invoices if inv.status.lower() == "overdue"]
    logger.info(f"Found {len(overdue_invoices)} overdue invoices")

    if not overdue_invoices:
        logger.info("No overdue invoices to process")
        return []

    # Process each invoice
    drafts_created = []
    updates_to_write = []

    for invoice in overdue_invoices:
        try:
            # Calculate days overdue and appropriate stage
            days = days_overdue(invoice.due_date, today)
            stage = stage_for(days)

            # Check if we should send a reminder
            if not should_send(stage, invoice.last_stage_sent, invoice.last_sent_at, today):
                logger.debug(
                    f"Skipping {invoice.invoice_id}: stage={stage}, "
                    f"last_stage={invoice.last_stage_sent}, last_sent={invoice.last_sent_at}"
                )
                continue

            # Build context for template
            context = {
                "name": invoice.client_name,
                "invoice_id": invoice.invoice_id,
                "amount": f"{invoice.amount:,.2f}",
                "currency": invoice.currency,
                "due_date": invoice.due_date.strftime("%b %d, %Y"),
            }

            # Render template to preview
            template_file = template_path_for(stage)
            subject, body = render_template(template_file, context)

            if settings.DRY_RUN:
                logger.info(
                    f"[DRY RUN] Would create draft for {invoice.invoice_id} "
                    f"(Stage {stage}d) to {invoice.client_email}: {subject}"
                )
            else:
                # Create the actual Gmail draft
                draft = create_draft_from_template(
                    to_email=invoice.client_email,
                    to_name=invoice.client_name,
                    stage=stage,
                    invoice_id=invoice.invoice_id,
                    amount=invoice.amount,
                    currency=invoice.currency,
                    due_date=invoice.due_date.strftime("%b %d, %Y"),
                )
                logger.info(
                    f"Created draft {draft['id']} for {invoice.invoice_id} "
                    f"(Stage {stage}d) to {invoice.client_email}"
                )

                # Track for write-back
                updates_to_write.append(
                    (invoice.invoice_id, stage, today.strftime("%Y-%m-%d"))
                )

            # Track what we created
            drafts_created.append(
                DraftCreated(
                    invoice_id=invoice.invoice_id,
                    stage=stage,
                    client_email=invoice.client_email,
                    client_name=invoice.client_name,
                    subject=subject,
                    amount=invoice.amount,
                    currency=invoice.currency,
                    days_overdue=days,
                )
            )

        except Exception as e:
            logger.error(f"Error processing invoice {invoice.invoice_id}: {e}")
            continue

    # Write back to Google Sheets
    if updates_to_write and not settings.DRY_RUN:
        try:
            rows_updated = write_back_invoices(updates_to_write)
            logger.info(f"Updated {rows_updated} rows in Google Sheets")
        except Exception as e:
            logger.error(f"Failed to write back to Google Sheets: {e}")
            # Don't raise - drafts were already created

    logger.info(f"Daily run complete. Created {len(drafts_created)} draft(s).")
    return drafts_created


def print_summary(drafts: List[DraftCreated]):
    """
    Print a nice summary table of created drafts

    Args:
        drafts: List of DraftCreated objects
    """
    if not drafts:
        print("\n✅ No drafts created - all invoices up to date!\n")
        return

    # Prepare table data
    table_data = []
    for draft in drafts:
        table_data.append([
            draft.invoice_id,
            f"Day {draft.stage}",
            draft.client_name,
            draft.client_email,
            f"${draft.amount:,.2f} {draft.currency}",
            f"{draft.days_overdue}d overdue",
        ])

    # Print table
    headers = ["Invoice ID", "Stage", "Client", "Email", "Amount", "Days Overdue"]
    print("\n" + "="*80)
    print(f"📧 Created {len(drafts)} Gmail Draft(s)")
    print("="*80)
    print(tabulate(table_data, headers=headers, tablefmt="simple"))
    print("="*80)

    if settings.DRY_RUN:
        print("\n⚠️  DRY RUN MODE - No actual drafts were created")
        print("   Set DRY_RUN=false in .env to create real drafts\n")
    else:
        print("\n✅ Drafts created in Gmail - review and send them!")
        print("   Open Gmail → Drafts to review and send\n")
