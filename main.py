#!/usr/bin/env python3
"""
Invoice Collector - Main Entry Point

Automated invoice collection system that creates Gmail drafts
for overdue invoice reminders based on a 6-stage escalation sequence.

Usage:
    python main.py              # Run daily collection job
    python main.py --dry-run    # Preview without creating drafts
    python main.py --help       # Show help
"""
import argparse
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from invoice_collector.scheduler import run_daily, print_summary
from invoice_collector.config import settings

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the invoice collector"""
    parser = argparse.ArgumentParser(
        description="Invoice Collection System - Creates Gmail drafts for overdue invoices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run with settings from .env
  python main.py --dry-run          # Preview what would be sent
  python main.py --verbose          # Show detailed logging

The system will:
1. Read overdue invoices from Google Sheets
2. Calculate appropriate reminder stage (7/14/21/28/35/42 days)
3. Create Gmail drafts (NOT auto-send) for review
4. Update tracking in Google Sheets

Daily usage:
  Run this script once per day (via cron or scheduler)
  Review drafts in Gmail and click Send
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mode - don't create actual drafts or update sheets"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress all output except errors"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    # Override DRY_RUN if specified
    if args.dry_run:
        settings.DRY_RUN = True

    try:
        # Run the daily job
        drafts_created, errors = run_daily()

        # Print summary
        if not args.quiet:
            print_summary(drafts_created, errors)

        # Exit with error code if there were failures
        if errors:
            logger.error(f"Completed with {len(errors)} error(s)")
            sys.exit(1)

        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
