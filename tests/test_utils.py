"""Tests for src/utils.py — validate_input (no Qt dependency)."""
import sys
from unittest.mock import MagicMock

# Mock PyQt5 and src.ui before importing utils — they aren't available in CI
sys.modules["PyQt5"] = MagicMock()
sys.modules["PyQt5.QtWidgets"] = MagicMock()
sys.modules["PyQt5.QtGui"] = MagicMock()
sys.modules["src.ui"] = MagicMock()

from src.utils import validate_input  # noqa: E402


class TestValidateInput:
    def test_valid_float(self):
        assert validate_input("3.14", 0.0) == 3.14

    def test_valid_int_string(self):
        assert validate_input("42", 0.0) == 42.0

    def test_invalid_string_returns_default(self):
        assert validate_input("abc", 99.0) == 99.0

    def test_empty_string_returns_default(self):
        assert validate_input("", 5.5) == 5.5

    def test_min_clamp(self):
        assert validate_input("0", 50.0, min_val=10) == 10

    def test_max_clamp(self):
        assert validate_input("300", 50.0, max_val=255) == 255

    def test_within_range(self):
        assert validate_input("100", 50.0, min_val=0, max_val=255) == 100

    def test_min_boundary(self):
        assert validate_input("10", 50.0, min_val=10) == 10

    def test_max_boundary(self):
        assert validate_input("255", 50.0, max_val=255) == 255

    def test_negative_value(self):
        assert validate_input("-5", 0.0) == -5.0

    def test_negative_clamped_to_min(self):
        assert validate_input("-5", 0.0, min_val=0) == 0
