"""
Data models for invoice tracking
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Invoice:
    """
    Represents an invoice with all tracking information

    Attributes:
        invoice_id: Unique identifier for the invoice
        client_name: Name of the client
        client_email: Email address for invoice reminders
        amount: Invoice amount (numeric)
        currency: Currency code (e.g., USD, EUR)
        due_date: Date the invoice is/was due
        sent_date: Date the invoice was originally sent
        status: Current status (e.g., "Overdue", "Paid", "Open")
        notes: Optional notes about the invoice
        last_stage_sent: Last reminder stage sent (7, 14, 21, 28, 35, or 42)
        last_sent_at: Date of last reminder sent
    """
    invoice_id: str
    client_name: str
    client_email: str
    amount: float
    currency: str
    due_date: date
    sent_date: date
    status: str
    notes: Optional[str] = ""
    last_stage_sent: Optional[int] = None
    last_sent_at: Optional[date] = None

    def __post_init__(self):
        """Validate invoice data after initialization"""
        if not self.invoice_id:
            raise ValueError("invoice_id cannot be empty")
        if not self.client_email or "@" not in self.client_email:
            raise ValueError(f"Invalid email for {self.client_name}: {self.client_email}")
        if self.amount < 0:
            raise ValueError(f"Amount cannot be negative: {self.amount}")

    def days_overdue(self, today: date = None) -> int:
        """Calculate how many days this invoice is overdue"""
        if today is None:
            today = date.today()
        return max(0, (today - self.due_date).days)

    def is_overdue(self, today: date = None) -> bool:
        """Check if this invoice is overdue"""
        return self.status.lower() == "overdue" or self.days_overdue(today) > 0


@dataclass
class DraftCreated:
    """
    Represents a draft that was created during a run
    """
    invoice_id: str
    stage: int
    client_email: str
    client_name: str
    subject: str
    amount: float
    currency: str
    days_overdue: int

    def __str__(self) -> str:
        return f"{self.invoice_id} | Stage {self.stage}d | {self.client_name} | ${self.amount:,.2f}"
