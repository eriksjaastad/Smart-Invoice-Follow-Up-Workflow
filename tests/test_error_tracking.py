"""
Tests for error tracking functionality
"""
import pytest
from datetime import date
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invoice_collector.scheduler import ErrorType, ProcessingError


class TestErrorType:
    """Test ErrorType enum"""

    def test_error_type_values(self):
        """Test that all error types have correct values"""
        assert ErrorType.SKIP_INVALID_DATA.value == "skip_invalid_data"
        assert ErrorType.DRAFT_FAILED.value == "draft_failed"
        assert ErrorType.WRITE_BACK_FAILED.value == "write_back_failed"
        assert ErrorType.READ_FAILED.value == "read_failed"

    def test_error_type_membership(self):
        """Test that error types can be compared"""
        error_type = ErrorType.DRAFT_FAILED
        assert error_type == ErrorType.DRAFT_FAILED
        assert error_type != ErrorType.SKIP_INVALID_DATA

    def test_error_type_iteration(self):
        """Test that we can iterate over error types"""
        error_types = list(ErrorType)
        assert len(error_types) == 4
        assert ErrorType.DRAFT_FAILED in error_types


class TestProcessingError:
    """Test ProcessingError dataclass"""

    def test_create_processing_error(self):
        """Test creating a processing error"""
        error = ProcessingError(
            invoice_id="INV-001",
            client_name="Test Client",
            error_message="Test error message",
            error_type=ErrorType.DRAFT_FAILED
        )

        assert error.invoice_id == "INV-001"
        assert error.client_name == "Test Client"
        assert error.error_message == "Test error message"
        assert error.error_type == ErrorType.DRAFT_FAILED

    def test_error_type_enum_required(self):
        """Test that error_type must be an ErrorType enum"""
        # This should work
        error = ProcessingError(
            invoice_id="INV-001",
            client_name="Test Client",
            error_message="Test error",
            error_type=ErrorType.WRITE_BACK_FAILED
        )
        assert isinstance(error.error_type, ErrorType)

    def test_error_message_formatting(self):
        """Test that error messages are preserved correctly"""
        long_message = "This is a very long error message " * 10
        error = ProcessingError(
            invoice_id="INV-001",
            client_name="Test Client",
            error_message=long_message,
            error_type=ErrorType.DRAFT_FAILED
        )

        assert error.error_message == long_message

        # Test truncation logic (as used in print_summary)
        truncated = error.error_message[:60] + "..." if len(error.error_message) > 60 else error.error_message
        assert len(truncated) <= 63  # 60 + "..."

    def test_multiple_errors_list(self):
        """Test creating a list of different error types"""
        errors = [
            ProcessingError("INV-001", "Client A", "Draft failed", ErrorType.DRAFT_FAILED),
            ProcessingError("INV-002", "Client B", "Write failed", ErrorType.WRITE_BACK_FAILED),
            ProcessingError("INV-003", "Client C", "Invalid data", ErrorType.SKIP_INVALID_DATA),
        ]

        assert len(errors) == 3
        assert errors[0].error_type == ErrorType.DRAFT_FAILED
        assert errors[1].error_type == ErrorType.WRITE_BACK_FAILED
        assert errors[2].error_type == ErrorType.SKIP_INVALID_DATA

    def test_error_grouping_by_type(self):
        """Test that errors can be grouped by type"""
        errors = [
            ProcessingError("INV-001", "Client A", "Error 1", ErrorType.DRAFT_FAILED),
            ProcessingError("INV-002", "Client B", "Error 2", ErrorType.DRAFT_FAILED),
            ProcessingError("INV-003", "Client C", "Error 3", ErrorType.WRITE_BACK_FAILED),
        ]

        draft_failures = [e for e in errors if e.error_type == ErrorType.DRAFT_FAILED]
        write_failures = [e for e in errors if e.error_type == ErrorType.WRITE_BACK_FAILED]

        assert len(draft_failures) == 2
        assert len(write_failures) == 1


class TestErrorTypeUsage:
    """Test real-world error type usage scenarios"""

    def test_error_type_string_conversion(self):
        """Test converting error type to string for display"""
        error = ProcessingError(
            invoice_id="INV-001",
            client_name="Test Client",
            error_message="Test error",
            error_type=ErrorType.DRAFT_FAILED
        )

        # This is how it's used in print_summary
        error_type_str = error.error_type.value
        assert error_type_str == "draft_failed"
        assert isinstance(error_type_str, str)

    def test_categorize_errors_by_severity(self):
        """Test categorizing errors by severity"""
        errors = [
            ProcessingError("INV-001", "A", "Msg", ErrorType.SKIP_INVALID_DATA),
            ProcessingError("INV-002", "B", "Msg", ErrorType.DRAFT_FAILED),
            ProcessingError("INV-003", "C", "Msg", ErrorType.WRITE_BACK_FAILED),
            ProcessingError("INV-004", "D", "Msg", ErrorType.READ_FAILED),
        ]

        # Critical errors (can't create drafts or read data)
        critical = [e for e in errors if e.error_type in
                   [ErrorType.DRAFT_FAILED, ErrorType.READ_FAILED]]

        # Warning level (data issues, tracking failures)
        warnings = [e for e in errors if e.error_type in
                   [ErrorType.SKIP_INVALID_DATA, ErrorType.WRITE_BACK_FAILED]]

        assert len(critical) == 2
        assert len(warnings) == 2
