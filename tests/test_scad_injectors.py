"""Tests for src/scad/injectors.py — SCAD template injection functions."""
import re
from src.scad.template import load_scad_template
from src.scad.injectors import (
    inject_general_settings,
    inject_dxf_options,
    inject_finger_scoops,
    inject_center_cutout,
    inject_divider_params,
    inject_border_and_text,
)


def _template():
    """Helper: load a fresh template for each test."""
    return load_scad_template()


class TestInjectGeneralSettings:
    def test_size_replaced(self):
        scad = inject_general_settings(_template(), 5, 2, 2.8)
        assert "size = [5, 2, 2.8];" in scad
        assert "size = [5, 2, 6];" not in scad

    def test_custom_size(self):
        scad = inject_general_settings(_template(), 7, 3, 3.5)
        assert "size = [7, 3, 3.5];" in scad

    def test_chamfer_disabled(self):
        scad = inject_general_settings(_template(), 5, 2, 2.8)
        assert "use_chamfered_extrude = false;" in scad
        assert "use_chamfered_extrude = true;" not in scad

    def test_chamfer_height_set(self):
        scad = inject_general_settings(_template(), 5, 2, 2.8)
        assert "chamfer_height = 3;" in scad
        assert "chamfer_height = 5;" not in scad

    def test_multiple_dxf_false_by_default(self):
        scad = inject_general_settings(_template(), 5, 2, 2.8)
        assert "multiple_dxf = false;" in scad

    def test_multiple_dxf_true_when_split(self):
        scad = inject_general_settings(_template(), 5, 2, 2.8, splitDXF=True)
        assert "multiple_dxf = true;" in scad


class TestInjectDxfOptions:
    def test_single_file_path(self):
        scad = inject_dxf_options(_template(), "tool_contour.dxf", splitDXF=False)
        assert 'dxf_file_path = "tool_contour.dxf";' in scad

    def test_single_file_replaces_default(self):
        scad = inject_dxf_options(_template(), "tool_contour.dxf", splitDXF=False)
        assert "examples/example.dxf" not in scad

    def test_backslash_conversion(self):
        scad = inject_dxf_options(_template(), "path\\to\\file.dxf", splitDXF=False)
        assert "path/to/file.dxf" in scad
        assert "\\" not in scad.split("dxf_file_path")[1].split(";")[0]

    def test_split_mode_creates_array(self):
        paths = ["testing_contour_1.dxf", "testing_contour_2.dxf"]
        scad = inject_dxf_options(_template(), paths, splitDXF=True)
        assert "dxf_file_paths = [" in scad
        assert '"testing_contour_1.dxf"' in scad
        assert '"testing_contour_2.dxf"' in scad

    def test_split_mode_has_cut_depths(self):
        paths = ["testing_contour_1.dxf"]
        scad = inject_dxf_options(_template(), paths, splitDXF=True)
        assert "dxf_cut_depths = [10];" in scad

    def test_split_mode_has_positions(self):
        paths = ["testing_contour_1.dxf"]
        scad = inject_dxf_options(_template(), paths, splitDXF=True)
        assert "position_1 = [" in scad
        assert "position = [position_1];" in scad

    def test_split_mode_has_section_adjustments(self):
        paths = ["testing_contour_1.dxf"]
        scad = inject_dxf_options(_template(), paths, splitDXF=True)
        assert "section_cut_depth_1 = [20, 15, 10];" in scad
        assert "section_parameters_1 = [40, 0, 0];" in scad

    def test_split_mode_sorts_by_contour_index(self):
        paths = ["test_contour_3.dxf", "test_contour_1.dxf", "test_contour_2.dxf"]
        scad = inject_dxf_options(_template(), paths, splitDXF=True)
        # Contour 1 should come before contour 3 in the output
        pos1 = scad.find("test_contour_1.dxf")
        pos3 = scad.find("test_contour_3.dxf")
        assert pos1 < pos3


class TestInjectFingerScoops:
    def test_scoop_positions_from_fixture(self, dxf_fixture_path, fixtures_dir):
        """Inject scoops using fixture DXF — should produce ±25.7mm."""
        scad = inject_finger_scoops(
            _template(), dxf_fixture_path, fixtures_dir, gridy_size=2
        )
        assert "use_finger_slots = true;" in scad
        assert "slot_pos_1 = [0, 25.7];" in scad
        assert "slot_pos_2 = [0, -25.7];" in scad

    def test_scoop_diameter_and_depth(self, dxf_fixture_path, fixtures_dir):
        scad = inject_finger_scoops(
            _template(), dxf_fixture_path, fixtures_dir, gridy_size=2
        )
        assert "scoop_diameter = 20;" in scad
        assert "scoop_depth = 10;" in scad

    def test_oval_shape(self, dxf_fixture_path, fixtures_dir):
        scad = inject_finger_scoops(
            _template(), dxf_fixture_path, fixtures_dir, gridy_size=2
        )
        assert 'slot_shape_1 = "oval";' in scad
        assert 'slot_shape_2 = "oval";' in scad

    def test_split_mode_scoops(self, dxf_fixture_path, fixtures_dir):
        """Split mode with 1 file should produce same scoop positions."""
        scad = inject_finger_scoops(
            _template(), [dxf_fixture_path], fixtures_dir, gridy_size=2, splitDXF=True
        )
        assert "slot_pos_1 = [0, 25.7];" in scad
        assert "slot_pos_2 = [0, -25.7];" in scad


class TestInjectCenterCutout:
    def test_adds_center_cutout_section(self):
        scad = inject_center_cutout(_template())
        assert "/* [Center Cutout] */" in scad

    def test_cutout_before_dxf_options(self):
        scad = inject_center_cutout(_template())
        cutout_pos = scad.find("/* [Center Cutout] */")
        dxf_pos = scad.find("/* [DXF Options] */")
        assert cutout_pos < dxf_pos

    def test_cutout_defaults(self):
        scad = inject_center_cutout(_template())
        assert "center_cutout_enabled = false;" in scad
        assert "center_cutout_width = 30;" in scad
        assert 'split_keep = "both";' in scad

    def test_cutout_geometry_added(self):
        scad = inject_center_cutout(_template())
        assert "// Center cutout for large tools" in scad
        assert "center_cutout_width" in scad


class TestInjectDividerParams:
    def test_divider_params_added(self):
        scad = inject_divider_params(_template())
        assert "divider_walls_enabled = false;" in scad
        assert "divider_walls = 0;" in scad
        assert "divider_clearance = 0;" in scad
        assert "divider_slot_spanning = false;" in scad

    def test_divider_after_aldo(self):
        scad = inject_divider_params(_template())
        aldo_pos = scad.find('text_font = "Aldo";')
        divider_pos = scad.find("divider_walls_enabled")
        assert aldo_pos < divider_pos


class TestInjectBorderAndText:
    def test_border_section_added(self):
        scad = inject_border_and_text(_template(), "TESTING", "blue", 5, 2)
        assert "/* [Border and Text] */" in scad

    def test_text_content(self):
        scad = inject_border_and_text(_template(), "TESTING", "blue", 5, 2)
        assert 'text_content = "TESTING";' in scad

    def test_text_position_5x2(self):
        """For 5x2: text_x = 5*42/2 - 37 = 68.0, text_y = 2*42/2 - 12 = 30.0"""
        scad = inject_border_and_text(_template(), "TESTING", "blue", 5, 2)
        assert "text_x = 68.0;" in scad
        assert "text_y = 30.0;" in scad

    def test_text_position_7x2(self):
        """For 7x2: text_x = 7*42/2 - 37 = 110.0, text_y = 30.0"""
        scad = inject_border_and_text(_template(), "CL 148-10", "blue", 7, 2)
        assert "text_x = 110.0;" in scad
        assert "text_y = 30.0;" in scad

    def test_border_defaults(self):
        scad = inject_border_and_text(_template(), "TESTING", "blue", 5, 2)
        assert "border_enabled = true;" in scad
        assert "border_height = 2;" in scad
        assert "text_rotation = 180;" in scad
        assert "border_text_size = 7;" in scad

    def test_color_in_geometry(self):
        scad = inject_border_and_text(_template(), "TEST", "blue", 5, 2)
        assert 'color("blue")' in scad

    def test_red_color(self):
        scad = inject_border_and_text(_template(), "MW 48-22-3420", "red", 6, 2)
        assert 'color("red")' in scad

    def test_border_before_section_adjustments(self):
        scad = inject_border_and_text(_template(), "TESTING", "blue", 5, 2)
        border_pos = scad.find("/* [Border and Text] */")
        section_pos = scad.find("/* [Section Adjustments] */")
        assert border_pos < section_pos

    def test_geometry_appended_at_end(self):
        scad = inject_border_and_text(_template(), "TESTING", "blue", 5, 2)
        assert scad.rstrip().endswith("}")
        assert "// === Colored border and text" in scad
