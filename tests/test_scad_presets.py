"""Tests for src/scad/presets.py — JSON presets file generation."""
import os
import json
import tempfile
from src.scad.presets import write_presets_json


class TestWritePresetsJson:
    def test_creates_json_file(self, tmp_path):
        scad_path = os.path.join(str(tmp_path), "test.scad")
        write_presets_json(scad_path, 5, 2)
        json_path = os.path.join(str(tmp_path), "test.json")
        assert os.path.exists(json_path)

    def test_valid_json(self, tmp_path):
        scad_path = os.path.join(str(tmp_path), "test.scad")
        write_presets_json(scad_path, 5, 2)
        json_path = os.path.join(str(tmp_path), "test.json")
        with open(json_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_has_parameter_sets(self, tmp_path):
        scad_path = os.path.join(str(tmp_path), "test.scad")
        write_presets_json(scad_path, 5, 2)
        json_path = os.path.join(str(tmp_path), "test.json")
        with open(json_path) as f:
            data = json.load(f)
        assert "parameterSets" in data
        assert "standard" in data["parameterSets"]

    def test_file_format_version(self, tmp_path):
        scad_path = os.path.join(str(tmp_path), "test.scad")
        write_presets_json(scad_path, 5, 2)
        json_path = os.path.join(str(tmp_path), "test.json")
        with open(json_path) as f:
            data = json.load(f)
        assert data["fileFormatVersion"] == "1"

    def test_size_5x2(self, tmp_path):
        scad_path = os.path.join(str(tmp_path), "test.scad")
        write_presets_json(scad_path, 5, 2)
        json_path = os.path.join(str(tmp_path), "test.json")
        with open(json_path) as f:
            data = json.load(f)
        assert data["parameterSets"]["standard"]["size"] == "[5, 2, 2.8]"

    def test_size_7x2(self, tmp_path):
        scad_path = os.path.join(str(tmp_path), "test.scad")
        write_presets_json(scad_path, 7, 2)
        json_path = os.path.join(str(tmp_path), "test.json")
        with open(json_path) as f:
            data = json.load(f)
        assert data["parameterSets"]["standard"]["size"] == "[7, 2, 2.8]"

    def test_standard_defaults(self, tmp_path):
        scad_path = os.path.join(str(tmp_path), "test.scad")
        write_presets_json(scad_path, 5, 2)
        json_path = os.path.join(str(tmp_path), "test.json")
        with open(json_path) as f:
            data = json.load(f)
        standard = data["parameterSets"]["standard"]
        assert standard["use_chamfered_extrude"] == "false"
        assert standard["lip_style"] == "none"
        assert standard["use_finger_slots"] == "false"
        assert standard["enable_magnets"] == "false"
        assert standard["filled_in"] == "enabled"
        assert standard["render_position"] == "center"

    def test_matches_fixture(self, tmp_path, json_fixture_path):
        """Compare generated JSON against the known-good fixture."""
        scad_path = os.path.join(str(tmp_path), "test.scad")
        write_presets_json(scad_path, 5, 2)
        json_path = os.path.join(str(tmp_path), "test.json")

        with open(json_path) as f:
            generated = json.load(f)
        with open(json_fixture_path) as f:
            fixture = json.load(f)

        assert generated == fixture
