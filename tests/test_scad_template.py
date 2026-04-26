"""Tests for src/scad/template.py — SCAD template loading."""
from src.scad.template import load_scad_template


class TestLoadScadTemplate:
    def test_loads_nonempty(self):
        scad = load_scad_template()
        assert len(scad) > 100

    def test_contains_general_settings(self):
        scad = load_scad_template()
        assert "/* [General Settings] */" in scad

    def test_contains_dxf_options(self):
        scad = load_scad_template()
        assert "/* [DXF Options] */" in scad

    def test_contains_finger_slot_options(self):
        scad = load_scad_template()
        assert "/* [Finger Slot Options] */" in scad

    def test_contains_section_adjustments(self):
        scad = load_scad_template()
        assert "/* [Section Adjustments] */" in scad

    def test_contains_shape_cutouts(self):
        scad = load_scad_template()
        assert "/* [Shape Cutouts] */" in scad

    def test_contains_default_size(self):
        scad = load_scad_template()
        assert "size = [5, 2, 6];" in scad

    def test_contains_default_dxf_path(self):
        scad = load_scad_template()
        assert 'dxf_file_path = "examples/example.dxf";' in scad

    def test_contains_default_position(self):
        scad = load_scad_template()
        assert "position = [[0, 0, 0]]; // .1" in scad

    def test_contains_chamfer_defaults(self):
        scad = load_scad_template()
        assert "use_chamfered_extrude = true;" in scad
        assert "chamfer_height = 5;" in scad

    def test_contains_multiple_dxf_flag(self):
        scad = load_scad_template()
        assert "multiple_dxf = false;" in scad

    def test_contains_text_font_aldo(self):
        scad = load_scad_template()
        assert 'text_font = "Aldo";' in scad
