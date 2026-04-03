"""
Invoice Pydantic schemas for validation.
These schemas validate invoice data from Google Sheets.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Invoice(BaseModel):
    """
    Schema for validating invoice data from Google Sheets.
    Used by daily processing to validate sheet data before creating drafts.
    """
    invoice_number: str = Field(..., min_length=1, max_length=100, description="Invoice number")
    client_name: str = Field(..., min_length=1, max_length=255, description="Client name")
    client_email: str = Field(..., min_length=1, max_length=255, description="Client email address")
    amount: Decimal = Field(..., gt=0, description="Invoice amount (must be positive)")
    due_date: date = Field(..., description="Invoice due date")
    sent_date: Optional[date] = Field(None, description="Date invoice was sent")
    paid: bool = Field(default=False, description="Whether invoice has been paid")
    
    @field_validator('client_email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Basic email format validation."""
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('invoice_number', 'client_name')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip whitespace from string fields."""
        return v.strip()
    
    def days_overdue(self, as_of: Optional[date] = None) -> int:
        """
        Calculate days overdue.
        Returns 0 if not overdue, positive number if overdue.
        """
        if self.paid:
            return 0
        
        check_date = as_of or date.today()
        if check_date <= self.due_date:
            return 0
        
        return (check_date - self.due_date).days

