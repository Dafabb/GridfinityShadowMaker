"""Shared pytest fixtures for GSM test suite."""
import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixtures_dir():
    """Path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def dxf_fixture_path():
    """Path to the CL 148-10 DXF contour fixture."""
    return os.path.join(FIXTURES_DIR, "testing_contour_1.dxf")


@pytest.fixture
def dxf_fixture_basename():
    """Just the filename of the DXF fixture."""
    return "testing_contour_1.dxf"


@pytest.fixture
def scad_fixture_path():
    """Path to the known-good SCAD output fixture."""
    return os.path.join(FIXTURES_DIR, "testing.scad")


@pytest.fixture
def json_fixture_path():
    """Path to the known-good JSON presets fixture."""
    return os.path.join(FIXTURES_DIR, "testing.json")


@pytest.fixture
def scad_template():
    """Load the raw SCAD template from the repo."""
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "Step 2 DXF to STL.scad"
    )
    with open(template_path, "r") as f:
        return f.read()


@pytest.fixture
def mock_console():
    """Mock console_text widget with .setText() method."""
    from unittest.mock import MagicMock
    console = MagicMock()
    console.setText = MagicMock()
    return console
