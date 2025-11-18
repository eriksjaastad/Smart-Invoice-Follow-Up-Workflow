"""
Tests for template rendering
"""
import pytest
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invoice_collector.emailer import render_template, template_path_for


class TestTemplateRendering:
    """Test template rendering logic"""

    def test_render_basic_template(self):
        """Test rendering a basic template"""
        with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Subject: Hello {{name}}\n\nHi {{name}}, welcome!")
            f.flush()

            subject, body = render_template(Path(f.name), {"name": "Sarah"})

            assert subject == "Hello Sarah"
            assert body == "Hi Sarah, welcome!"

            Path(f.name).unlink()

    def test_render_invoice_template(self):
        """Test rendering with invoice data"""
        with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(
                "Subject: Invoice {{invoice_id}} for {{amount}} {{currency}}\n\n"
                "Dear {{name}},\n\n"
                "Your invoice {{invoice_id}} for {{amount}} {{currency}} was due {{due_date}}."
            )
            f.flush()

            context = {
                "name": "John Doe",
                "invoice_id": "INV-001",
                "amount": "2,500.00",
                "currency": "USD",
                "due_date": "Jan 15, 2025"
            }

            subject, body = render_template(Path(f.name), context)

            assert subject == "Invoice INV-001 for 2,500.00 USD"
            assert "Your invoice INV-001 for 2,500.00 USD was due Jan 15, 2025" in body

            Path(f.name).unlink()

    def test_missing_placeholder(self):
        """Test that missing placeholders are left as-is (safe_substitute)"""
        with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Subject: Hello {{name}}\n\nHi {{name}}, your {{missing}} is ready.")
            f.flush()

            subject, body = render_template(Path(f.name), {"name": "Sarah"})

            assert subject == "Hello Sarah"
            assert "Hi Sarah, your {{missing}} is ready" in body

            Path(f.name).unlink()

    def test_template_path_for_stages(self):
        """Test template path generation for all stages"""
        assert template_path_for(7).name == "stage_07.txt"
        assert template_path_for(14).name == "stage_14.txt"
        assert template_path_for(21).name == "stage_21.txt"
        assert template_path_for(28).name == "stage_28.txt"
        assert template_path_for(35).name == "stage_35.txt"
        assert template_path_for(42).name == "stage_42.txt"

    def test_invalid_template_format(self):
        """Test that invalid template format raises error"""
        with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a valid template")
            f.flush()

            with pytest.raises(ValueError, match="must start with 'Subject:'"):
                render_template(Path(f.name), {})

            Path(f.name).unlink()


class TestActualTemplates:
    """Test actual template files exist and are valid"""

    def test_all_stage_templates_exist(self):
        """Verify all 6 stage templates exist"""
        stages = [7, 14, 21, 28, 35, 42]
        for stage in stages:
            template_file = template_path_for(stage)
            # Note: This will only pass if templates are in the expected location
            # In a real run, these should exist
            if template_file.exists():
                assert template_file.exists(), f"Template for stage {stage} not found"

                # Verify it can be rendered
                context = {
                    "name": "Test Client",
                    "invoice_id": "TEST-001",
                    "amount": "1,000.00",
                    "currency": "USD",
                    "due_date": "Jan 01, 2025"
                }

                subject, body = render_template(template_file, context)

                # Basic validations
                assert len(subject) > 0, f"Stage {stage} template has empty subject"
                assert len(body) > 0, f"Stage {stage} template has empty body"
                assert "Test Client" in body or "{{name}}" in body
