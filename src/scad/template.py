"""Load the base SCAD template file."""
import os


def load_scad_template():
    """Load the base SCAD template file."""
    template_path = os.path.join(os.path.dirname(__file__), "..", "..", "Step 2 DXF to STL.scad")
    with open(template_path, 'r') as f:
        return f.read()
