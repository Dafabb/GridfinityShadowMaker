"""OpenSCAD generation modules."""
from src.scad.template import load_scad_template
from src.scad.injectors import (
    inject_general_settings,
    inject_dxf_options,
    inject_finger_scoops,
    inject_center_cutout,
    inject_divider_params,
    inject_border_and_text,
)
from src.scad.generators import (
    generate_bin_scad,
    generate_test_slab,
)
from src.scad.presets import write_presets_json
