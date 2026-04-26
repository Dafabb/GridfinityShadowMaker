"""Tests for src/dxf/export.py — load_offset_positions."""
import os
import pickle
import tempfile
from src.dxf.export import load_offset_positions


class TestLoadOffsetPositions:
    def test_no_pickle_returns_defaults(self):
        """With no pickle file, should return [[0,0]] * num_files."""
        result = load_offset_positions(3)
        assert result == [[0, 0], [0, 0], [0, 0]]

    def test_defaults_match_count(self):
        result = load_offset_positions(5)
        assert len(result) == 5
        assert all(pos == [0, 0] for pos in result)

    def test_single_file_default(self):
        result = load_offset_positions(1)
        assert result == [[0, 0]]
