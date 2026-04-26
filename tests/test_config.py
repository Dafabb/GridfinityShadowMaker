"""Tests for src/config.py — constants and defaults."""
from src.config import (
    DEFAULT_THRESHOLD,
    DEFAULT_OFFSET,
    DEFAULT_TOKEN,
    DEFAULT_RESOLUTION,
    BRAND_CODES,
    TOKEN_SUB_10,
    TOKEN_10_INCH,
    DEFAULT_BIN_HEIGHT,
    DEFAULT_CHAMFER_HEIGHT,
    FILAMENT_CHANGE_HEIGHT,
)


class TestDefaults:
    def test_threshold(self):
        assert DEFAULT_THRESHOLD == 145

    def test_offset(self):
        assert DEFAULT_OFFSET == 0.04

    def test_token(self):
        assert DEFAULT_TOKEN == 2.89

    def test_resolution(self):
        assert DEFAULT_RESOLUTION == 20


class TestTokenSizes:
    def test_sub_10_token(self):
        assert TOKEN_SUB_10 == 2.89

    def test_10_inch_token(self):
        assert TOKEN_10_INCH == 2.82


class TestBrandCodes:
    def test_channellock(self):
        assert BRAND_CODES["CL"] == "Channellock"

    def test_milwaukee(self):
        assert BRAND_CODES["MW"] == "Milwaukee"

    def test_stanley(self):
        assert BRAND_CODES["ST"] == "Stanley"

    def test_all_brands_present(self):
        expected = {"CL", "MW", "DW", "WRA", "TEK", "KNX", "HDX", "ST"}
        assert set(BRAND_CODES.keys()) == expected


class TestGridfinityDefaults:
    def test_bin_height(self):
        assert DEFAULT_BIN_HEIGHT == 2.8

    def test_chamfer_height(self):
        assert DEFAULT_CHAMFER_HEIGHT == 3

    def test_filament_change_height(self):
        assert FILAMENT_CHANGE_HEIGHT == 19.8
