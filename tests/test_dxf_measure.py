"""Tests for src/dxf/measure.py — DXF measurement and scoop positions."""
import os
import ezdxf
from src.dxf.measure import (
    _collect_dxf_points,
    measure_dxf_bounding_box,
    calculate_scoop_positions,
)


class TestCollectDxfPoints:
    """Tests for _collect_dxf_points with the real DXF fixture."""

    def test_returns_points(self, dxf_fixture_path):
        doc = ezdxf.readfile(dxf_fixture_path)
        msp = doc.modelspace()
        pts = _collect_dxf_points(msp)
        assert len(pts) > 0

    def test_returns_tuples(self, dxf_fixture_path):
        doc = ezdxf.readfile(dxf_fixture_path)
        msp = doc.modelspace()
        pts = _collect_dxf_points(msp)
        for pt in pts:
            assert isinstance(pt, tuple)
            assert len(pt) == 2

    def test_known_point_count(self, dxf_fixture_path):
        """Fixture has 1 LWPOLYLINE with 194 points."""
        doc = ezdxf.readfile(dxf_fixture_path)
        msp = doc.modelspace()
        pts = _collect_dxf_points(msp)
        assert len(pts) == 194

    def test_bounding_box_range(self, dxf_fixture_path):
        """Points should span roughly ±3.7 in X and ±1.0 in Y (inches)."""
        doc = ezdxf.readfile(dxf_fixture_path)
        msp = doc.modelspace()
        pts = _collect_dxf_points(msp)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        # X range ~7.4 inches, Y range ~2.0 inches
        assert max(xs) - min(xs) > 7.0
        assert max(ys) - min(ys) > 1.5

    def test_empty_modelspace(self):
        """Empty DXF should return empty list."""
        doc = ezdxf.new()
        msp = doc.modelspace()
        pts = _collect_dxf_points(msp)
        assert pts == []


class TestMeasureDxfBoundingBox:
    """Tests for measure_dxf_bounding_box with the real DXF fixture."""

    def test_single_file_returns_cutout_string(self, dxf_fixture_path, fixtures_dir):
        result = measure_dxf_bounding_box(
            dxf_fixture_path, fixtures_dir, splitDXF=False
        )
        assert "Cutout:" in result
        assert "mm" in result

    def test_single_file_dimensions(self, dxf_fixture_path, fixtures_dir):
        """Fixture should measure ~188.4mm x 51.4mm."""
        result = measure_dxf_bounding_box(
            dxf_fixture_path, fixtures_dir, splitDXF=False
        )
        # Parse "Cutout: 188.4mm x 51.4mm"
        import re
        m = re.search(r"(\d+\.\d+)mm x (\d+\.\d+)mm", result)
        assert m is not None
        length = float(m.group(1))
        width = float(m.group(2))
        assert abs(length - 188.4) < 1.0
        assert abs(width - 51.4) < 1.0

    def test_split_mode_single_file_list(self, dxf_fixture_path, fixtures_dir):
        """Split mode with a list of 1 DXF should return same result."""
        single = measure_dxf_bounding_box(
            dxf_fixture_path, fixtures_dir, splitDXF=False
        )
        split = measure_dxf_bounding_box(
            [dxf_fixture_path], fixtures_dir, splitDXF=True
        )
        assert "Cutout:" in split
        # Dimensions should match (parsing both)
        import re
        m1 = re.search(r"(\d+\.\d+)mm x (\d+\.\d+)mm", single)
        m2 = re.search(r"(\d+\.\d+)mm x (\d+\.\d+)mm", split)
        assert m1 is not None and m2 is not None
        assert m1.group(1) == m2.group(1)
        assert m1.group(2) == m2.group(2)

    def test_nonexistent_file_returns_empty(self, fixtures_dir):
        result = measure_dxf_bounding_box(
            "nonexistent.dxf", fixtures_dir, splitDXF=False
        )
        assert result == ""

    def test_split_empty_list_returns_empty(self, fixtures_dir):
        result = measure_dxf_bounding_box([], fixtures_dir, splitDXF=True)
        assert result == ""


class TestCalculateScoopPositions:
    """Tests for calculate_scoop_positions with the real DXF fixture."""

    def test_returns_tuple_of_two(self, dxf_fixture_path, fixtures_dir):
        result = calculate_scoop_positions(
            dxf_fixture_path, fixtures_dir, gridy_size=2, splitDXF=False
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_known_scoop_positions(self, dxf_fixture_path, fixtures_dir):
        """Fixture produces scoop positions of ~25.7mm on both sides."""
        y_pos, y_neg = calculate_scoop_positions(
            dxf_fixture_path, fixtures_dir, gridy_size=2, splitDXF=False
        )
        assert abs(y_pos - 25.7) < 0.5
        assert abs(y_neg - 25.7) < 0.5

    def test_split_mode_matches_single(self, dxf_fixture_path, fixtures_dir):
        """Split mode with 1 file should match single-file mode."""
        single = calculate_scoop_positions(
            dxf_fixture_path, fixtures_dir, gridy_size=2, splitDXF=False
        )
        split = calculate_scoop_positions(
            [dxf_fixture_path], fixtures_dir, gridy_size=2, splitDXF=True
        )
        assert abs(single[0] - split[0]) < 0.1
        assert abs(single[1] - split[1]) < 0.1

    def test_fallback_on_missing_file(self, fixtures_dir):
        """Missing file should return default scoop positions (gridy*42/2)."""
        y_pos, y_neg = calculate_scoop_positions(
            "nonexistent.dxf", fixtures_dir, gridy_size=2, splitDXF=False
        )
        expected = 2 * 42 / 2  # 42mm
        assert y_pos == expected
        assert y_neg == expected
