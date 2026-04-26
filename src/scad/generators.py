"""Main SCAD file assemblers for bin and test slab generation."""
import os
import traceback
from src.scad.template import load_scad_template
from src.scad.injectors import (
    inject_general_settings,
    inject_dxf_options,
    inject_finger_scoops,
    inject_center_cutout,
    inject_divider_params,
    inject_border_and_text,
)
from src.scad.presets import write_presets_json
from src.dxf.measure import measure_dxf_bounding_box
import src.utils as _utils


def generate_bin_scad(dxf_path, gridx_size, gridy_size, console_text, file_name,
                      folder_name, splitDXF=False, border_color="blue",
                      generate_test_slab=True):
    """Assemble a Gridfinity bin SCAD file from template + injected sections.

    Pipeline:
        load template
        → inject_general_settings   (size, chamfer, multiple_dxf)
        → inject_dxf_options         (file paths, positions, sections)
        → inject_finger_scoops       (oval scoops at tool outline edges)
        → inject_divider_params      (required module params)
        → inject_border_and_text     (colored border + label in Customizer)
        → write .scad + .json
    """
    try:
        # Setup output directory
        script_directory = os.path.dirname(os.path.abspath(__file__))
        design_files_directory = os.path.join(script_directory, "..", "..", folder_name)
        os.makedirs(design_files_directory, exist_ok=True)
        scad_file_path = os.path.join(design_files_directory, f"{file_name}.scad")
        _utils.scad_file_path = scad_file_path

        # Build SCAD content
        scad = load_scad_template()
        scad = inject_general_settings(scad, gridx_size, gridy_size, splitDXF=splitDXF)
        scad = inject_dxf_options(scad, dxf_path, splitDXF)
        scad = inject_finger_scoops(scad, dxf_path, design_files_directory, gridy_size, splitDXF)
        scad = inject_center_cutout(scad)
        scad = inject_divider_params(scad)

        label_text = file_name.upper().replace('_', ' ')
        scad = inject_border_and_text(scad, label_text, border_color, gridx_size, gridy_size)

        # Write files
        with open(scad_file_path, 'w') as f:
            f.write(scad)
        write_presets_json(scad_file_path, gridx_size, gridy_size)

        # Report
        dim_text = measure_dxf_bounding_box(dxf_path, design_files_directory, splitDXF)
        console_text.setText(f"Bin SCAD written to: {os.path.basename(scad_file_path)}{dim_text}")

    except Exception as e:
        console_text.setText(f"Error generating bin SCAD: {str(e)}")
        print(traceback.format_exc())


def generate_test_slab(dxf_path, gridx_size, gridy_size, console_text, file_name,
                       folder_name, splitDXF=False):
    """Generate a thin test slab SCAD for fit validation before full print."""
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__))
        design_files_directory = os.path.join(script_directory, "..", "..", folder_name)
        os.makedirs(design_files_directory, exist_ok=True)
        test_slab_path = os.path.join(design_files_directory, f"{file_name}_test_slab.scad")

        # Collect DXF file references
        if splitDXF and isinstance(dxf_path, list):
            dxf_files = [p.replace("\\", "/") for p in dxf_path]
        else:
            dxf_files = [dxf_path.replace("\\", "/")]

        dxf_cuts = "\n".join([
            f'    scale([25.4, 25.4])\n'
            f'        import("{dxf}");'
            for dxf in dxf_files
        ])

        test_slab_content = (
            f"// Test slab for fit validation\n"
            f"// Drop tool onto slab to check pocket fit before full print\n\n"
            f"/* [Slab Settings] */\n"
            f"margin = 10; // [5:1:30]\n"
            f"slab_height = 0.60; // [0.20:0.20:2.0]\n\n"
            f"/* [Center Cutout] */\n"
            f"center_cutout_enabled = false; // true or false\n"
            f"center_cutout_width = 1; // [1:1:150]\n"
            f"split_keep = \"both\"; // [both, left, right]\n\n"
            f"module end_of_customizer_opts() {{}}\n\n"
            f"difference() {{\n"
            f"    linear_extrude(height = slab_height)\n"
            f"    difference() {{\n"
            f"        offset(delta = margin)\n"
            f"            scale([25.4, 25.4])\n"
            f"                import(\"{dxf_files[0]}\");\n"
            f"{dxf_cuts}\n"
            f"    }}\n"
            f"    if (center_cutout_enabled) {{\n"
            f"        translate([-center_cutout_width/2, -500, -1])\n"
            f"            cube([center_cutout_width, 1000, slab_height + 10]);\n"
            f"        if (split_keep == \"left\") {{\n"
            f"            translate([center_cutout_width/2, -500, -1])\n"
            f"                cube([500, 1000, slab_height + 10]);\n"
            f"        }}\n"
            f"        if (split_keep == \"right\") {{\n"
            f"            translate([-(500 + center_cutout_width/2), -500, -1])\n"
            f"                cube([500, 1000, slab_height + 10]);\n"
            f"        }}\n"
            f"    }}\n"
            f"}}\n"
        )

        with open(test_slab_path, 'w') as test_file:
            test_file.write(test_slab_content)

        dim_text = measure_dxf_bounding_box(dxf_path, design_files_directory, splitDXF)
        console_text.setText(f"Test slab written to: {os.path.basename(test_slab_path)}{dim_text}")

    except Exception as e:
        console_text.setText(f"Error generating test slab: {str(e)}")
        print(traceback.format_exc())
