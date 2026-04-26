"""OpenSCAD Customizer presets JSON file generation."""
import json


def write_presets_json(scad_file_path, gridx, gridy):
    """Write OpenSCAD Customizer presets JSON alongside SCAD file."""
    presets_path = scad_file_path.replace('.scad', '.json')
    presets = {
        "parameterSets": {
            "standard": {
                "size": f"[{gridx}, {gridy}, 2.8]",
                "use_chamfered_extrude": "false",
                "lip_style": "none",
                "use_finger_slots": "false",
                "use_section_cut": "false",
                "add_shape_data": "false",
                "half_pitch": "false",
                "enable_magnets": "false",
                "include_post": "false",
                "include_cutout": "false",
                "include_label": "false",
                "text_1": "false",
                "text_2": "false",
                "filled_in": "enabled",
                "render_position": "center"
            }
        },
        "fileFormatVersion": "1"
    }
    with open(presets_path, 'w') as f:
        json.dump(presets, f, indent=2)
