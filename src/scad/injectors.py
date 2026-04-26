"""SCAD template injection functions for Gridfinity bin generation."""
import os
import re
from src.dxf.export import load_offset_positions
from src.dxf.measure import calculate_scoop_positions


def inject_general_settings(scad, gridx, gridy, height=2.8, splitDXF=False):
    """Inject size, chamfer disable, and multiple_dxf flag."""
    scad = scad.replace('size = [5, 2, 6];', f'size = [{gridx}, {gridy}, {height}];')
    scad = scad.replace('multiple_dxf = false;', f'multiple_dxf = {str(splitDXF).lower()};')
    scad = scad.replace('use_chamfered_extrude = true;', 'use_chamfered_extrude = false;')
    scad = scad.replace('chamfer_height = 5;', 'chamfer_height = 3;')
    return scad


def _build_split_dxf_block(scad, dxf_paths):
    """Build SCAD block for split DXF multi-contour tools."""
    dxf_file_paths = [p.replace("\\", "/") for p in dxf_paths]

    # Sort by contour index
    def contour_index(path):
        m = re.search(r'_contour_(\d+)\.dxf$', os.path.basename(path))
        return int(m.group(1)) if m else 0
    dxf_file_paths.sort(key=contour_index)

    num_files = len(dxf_file_paths)

    # --- DXF file paths ---
    dxf_paths_scad = (
        'dxf_file_paths = [\n'
        + ',\n'.join([f'"{p}"' for p in dxf_file_paths])
        + '\n];\n'
    )

    # --- Cut depths (chunked into arrays of 4 for OpenSCAD limits) ---
    cut_depths = ["10"] * num_files
    cut_depth_arrays = [cut_depths[i:i+4] for i in range(0, len(cut_depths), 4)]
    dxf_cut_depths_scad = ""
    concat_line = ""
    if len(cut_depth_arrays) == 1:
        dxf_cut_depths_scad = f"dxf_cut_depths = [{', '.join(cut_depth_arrays[0])}];\n"
    else:
        array_names = []
        for idx, arr in enumerate(cut_depth_arrays):
            name = f'dxf_cut_depths_{idx+1}'
            array_names.append(name)
            dxf_cut_depths_scad += f"{name} = [{', '.join(arr)}];\n"
        concat_line = f"dxf_cut_depths = concat({', '.join(array_names)});\n"

    # --- Section blocks ---
    section_cut_depth_names = []
    section_param_names = []
    section_blocks = []
    for idx in range(num_files):
        cut_name = f'section_cut_depth_{idx+1}'
        param_name = f'section_parameters_{idx+1}'
        section_cut_depth_names.append(cut_name)
        section_param_names.append(param_name)
        section_blocks.append(f'{cut_name} = [20, 15, 10];\n{param_name} = [40, 0, 0];')
    section_cut_depth_concat = f"section_cut_depth = [{', '.join(section_cut_depth_names)}];\n"
    section_parameters_concat = f"section_parameters = [{', '.join(section_param_names)}];\n"

    # --- Positions from pickle ---
    pos_xy = load_offset_positions(num_files)
    position_lines = []
    for idx in range(num_files):
        position_lines.append(
            f'position_{idx+1} = [{pos_xy[idx][0]:.6f},{pos_xy[idx][1]:.6f},0]; // .1'
        )
    position_array = f"position = [{', '.join([f'position_{i+1}' for i in range(num_files)])}];\n"

    # --- Apply replacements ---
    scad = scad.replace(
        'position = [[0, 0, 0]]; // .1',
        '\n'.join(position_lines) + '\n' + position_array
    )

    scad_block = (
        dxf_paths_scad + dxf_cut_depths_scad + concat_line
        + '// dxf_file_path replaced by dxf_file_paths'
    )
    scad = scad.replace('dxf_file_path = "examples/example.dxf";', scad_block)

    section_marker = '/* [Section Adjustments] */'
    if section_marker in scad:
        parts = scad.split(section_marker, 1)
        new_block = '\nuse_section_cut = false; // true or false\n'
        for block in section_blocks:
            new_block += block + '\n'
        new_block += section_cut_depth_concat + section_parameters_concat
        scad = parts[0] + section_marker + new_block + parts[1]

    return scad


def inject_dxf_options(scad, dxf_path, splitDXF=False):
    """Inject DXF file paths, cut depths, positions, and section adjustments."""
    if splitDXF and isinstance(dxf_path, list):
        return _build_split_dxf_block(scad, dxf_path)
    else:
        dxf_path = dxf_path.replace("\\", "/")
        return scad.replace(
            'dxf_file_path = "examples/example.dxf";',
            f'dxf_file_path = "{dxf_path}";'
        )


def inject_finger_scoops(scad, dxf_path, folder_path, gridy_size, splitDXF=False):
    """Inject finger scoop parameters using built-in finger slot system.

    Positions are calculated from the DXF tool outline edges so scoops sit
    at the actual tool boundary, not the bin boundary.

    NOTE: For splitDXF, this overwrites any per-contour finger slots from
    _inject_dxf_split. TODO: Support per-contour scoops for split DXF.
    """
    scoop_y_pos, scoop_y_neg = calculate_scoop_positions(
        dxf_path, folder_path, gridy_size, splitDXF
    )
    replacement = (
        f'/* [Finger Slot Options] */\n'
        f'use_finger_slots = true; // true or false\n'
        f'scoop_diameter = 20; // [10:1:40]\n'
        f'scoop_depth = 10; // [5:1:30]\n'
        f'slot_shape_1 = "oval"; // [none, rectangle, oval, scoop, triangle, keyhole, teardrop]\n'
        f'slot_params_1 = [scoop_diameter, scoop_diameter, scoop_depth, 0]; // length, width, height, rotation\n'
        f'slot_pos_1 = [0, {scoop_y_pos:.1f}]; // [x, y] in mm\n'
        f'slot_shape_2 = "oval"; // [none, rectangle, oval, scoop, triangle, keyhole, teardrop]\n'
        f'slot_params_2 = [scoop_diameter, scoop_diameter, scoop_depth, 0];\n'
        f'slot_pos_2 = [0, -{scoop_y_neg:.1f}];\n'
        f'slot_shape = [slot_shape_1, slot_shape_2];\n'
        f'slot_params = [slot_params_1, slot_params_2];\n'
        f'slot_pos = [slot_pos_1, slot_pos_2];'
    )
    scad = re.sub(
        r'/\* \[Finger Slot Options\] \*/.*?slot_pos = \[.*?\];',
        replacement, scad, flags=re.DOTALL
    )
    return scad


def inject_center_cutout(scad):
    """Add center cutout option for large tools."""
    params = (
        '\n/* [Center Cutout] */\n'
        'center_cutout_enabled = false; // true or false\n'
        'center_cutout_width = 30; // [10:5:150]\n'
        'split_keep = "both"; // [both, left, right]\n'
    )

    # Determines where to insert our Customizer settings
    scad = scad.replace(
        '/* [DXF Options] */',
        params + '/* [DXF Options] */'
    )

    # Cut a rectangle through the center, inside the render difference block
    cutout = (
        '\n// Center cutout for large tools\n'
        'if (center_cutout_enabled) {\n'
        '    translate([-center_cutout_width/2, -(depth[0]*42 + 10)/2, -1])\n'
        '        cube([center_cutout_width, depth[0]*42 + 10, height[0]*7 + 10]);\n'
        '    if (split_keep == "left") {\n'
        '        translate([center_cutout_width/2, -(depth[0]*42 + 10)/2, -1])\n'
        '            cube([width[0]*42, depth[0]*42 + 10, height[0]*7 + 10]);\n'
        '    }\n'
        '    if (split_keep == "right") {\n'
        '        translate([-(width[0]*42 + center_cutout_width/2), -(depth[0]*42 + 10)/2, -1])\n'
        '            cube([width[0]*42, depth[0]*42 + 10, height[0]*7 + 10]);\n'
        '    }\n'
        '}\n'
    )

    scad = scad.replace(
        '}\n\n// Conditionally extrude',
        cutout + '}\n\n// Conditionally extrude'
    )
    return scad


def inject_divider_params(scad):
    """Add divider parameters required for gridfinity_cup module."""
    divider_params = (
        '\ndivider_walls_enabled = false;\n'
        'divider_walls = 0;\n'
        'divider_headroom = 0;\n'
        'divider_walls_support_thickness = 0;\n'
        'divider_wall_slot_size = 0;\n'
        'divider_walls_spacing = 0;\n'
        'divider_walls_thickness = 0;\n'
        'divider_clearance = 0;\n'
        'divider_slot_spanning = false;\n'
    )
    return scad.replace('text_font = "Aldo";', 'text_font = "Aldo";\n' + divider_params)


def inject_border_and_text(scad, label_text, border_color, gridx, gridy):
    """Inject border/text params into Customizer and append geometry.

    Params are inserted before Section Adjustments to keep Customizer order:
    General → DXF → Finger Slot → Border and Text → (rest collapsed below)
    """
    text_x = gridx * 42 / 2 - 37
    text_y = gridy * 42 / 2 - 12
    params = (
        f'\n/* [Border and Text] */\n'
        f'border_enabled = true; // true or false\n'
        f'border_height = 2; // [1:0.5:6]\n'
        f'text_enabled = true; // true or false\n'
        f'text_content = "{label_text}";\n'
        f'border_text_size = 7; // [4:1:14]\n'
        f'text_x = {text_x:.1f}; // [-200:1:200]\n'
        f'text_y = {text_y:.1f}; // [-200:1:200]\n'
        f'text_rotation = 180; // [0:90:360]\n'
    )

    geometry = f"""
// === Colored border and text with center cutout support ===
difference() {{
    union() {{
        if (border_enabled) {{
            color("{border_color}")
            translate([0, 0, height[0]*7])
            linear_extrude(height = border_height)
            difference() {{
                offset(r = 3.75)
                    square([width[0]*42 - 0.5 - 7.5, depth[0]*42 - 0.5 - 7.5], center=true);
                offset(r = 3.75)
                    square([width[0]*42 - 4.5 - 7.5, depth[0]*42 - 4.5 - 7.5], center=true);
            }}
        }}
        // === Tool label text ===
        if (text_enabled) {{
            color("{border_color}")
            translate([text_x, text_y, height[0]*7])
            linear_extrude(height = border_height)
            rotate([0, 0, text_rotation])
            text(text_content, size = border_text_size, font = "Arial Rounded MT Bold", halign = "center", valign = "center");
        }}
    }}
    // Center cutout through border/text
    if (center_cutout_enabled) {{
        translate([-center_cutout_width/2, -(depth[0]*42 + 10)/2, height[0]*7 - 1])
            cube([center_cutout_width, depth[0]*42 + 10, border_height + 10]);
        if (split_keep == "left") {{
            translate([center_cutout_width/2, -(depth[0]*42 + 10)/2, height[0]*7 - 1])
                cube([width[0]*42, depth[0]*42 + 10, border_height + 10]);
        }}
        if (split_keep == "right") {{
            translate([-(width[0]*42 + center_cutout_width/2), -(depth[0]*42 + 10)/2, height[0]*7 - 1])
                cube([width[0]*42, depth[0]*42 + 10, border_height + 10]);
        }}
    }}
}}
"""

    scad = scad.replace(
        '/* [Section Adjustments] */',
        params + '\n/* [Section Adjustments] */'
    )
    scad += geometry
    return scad
