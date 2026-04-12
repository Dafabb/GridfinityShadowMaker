import cv2
import numpy as np
import math
import ezdxf
import pyperclip
import os
import re
import json
import pickle
import tempfile
import subprocess
import traceback
import time
import concurrent.futures
from PIL import Image
from PyQt5 import QtWidgets, QtGui
from src.ui import Ui_MainWindow  # type: ignore

scad_file_path = None

# ============================================================
# Utility Functions
# ============================================================
def validate_input(value, default, min_val=None, max_val=None):
    try:
        value = float(value)
        if min_val is not None and value < min_val:
            value = min_val
        if max_val is not None and value > max_val:
            value = max_val
    except ValueError:
        value = default
    return value

def get_threshold_input(threshold_entry, offset_entry, token_entry, resolution_entry):
    global offset, token, resolution
    threshold_input = validate_input(threshold_entry.text(), 110, 0, 255)
    offset = validate_input(offset_entry.text(), 0.1)
    token = validate_input(token_entry.text(), 2.000)
    resolution = validate_input(resolution_entry.text(), 10)
    return threshold_input

# ============================================================
# Image Processing & Display
# ============================================================
def clear_canvas(canvas, keep_original=False):
    try:
        canvas.scene().clear()
        if keep_original and hasattr(canvas, 'image1'):
            canvas.scene().addPixmap(canvas.image1).setPos(0, 0)
            canvas.scene().addText("Original", QtGui.QFont("Helvetica", 16)).setPos(canvas.width() // 6, 5)
        canvas.update()
    except Exception as e:
        print(f"Error clearing canvas: {str(e)}")
        print(traceback.format_exc())

def preprocess_image(image, threshold_input):
    if isinstance(image, str):
        image = cv2.imread(image)
    imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(imgray, threshold_input, 255, cv2.THRESH_BINARY)
    thresh = cv2.bitwise_not(thresh)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return image, thresh

def find_max_p2d_ratio_contour(contours):
    max_p2d_ratio = 0
    max_p2d_contour = None
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        diameter = calculate_diameter(contour)
        if diameter == 0:
            continue
        p2d_ratio = perimeter / diameter
        if p2d_ratio > max_p2d_ratio:
            max_p2d_ratio = p2d_ratio
            max_p2d_contour = contour
    return max_p2d_contour, max_p2d_ratio

def calculate_diameter(contour):
    (x, y), radius = cv2.minEnclosingCircle(contour)
    return 2 * radius


def display_contours(image, contours, canvas, region, caption, color):
    contours_img = image.copy()
    thickness = max(1, min(image.shape[0], image.shape[1]) // 200)
    cv2.drawContours(contours_img, contours, -1, color, thickness)
    display_image_on_canvas(contours_img, canvas, region, caption)


def display_image_on_canvas(image, canvas, region, caption):
    try:
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)

        canvas_width = canvas.width() // 3
        canvas_height = canvas.height() - 50

        scale_factor = min(canvas_width / img.width, canvas_height / img.height)
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)

        img = img.resize((new_width, new_height), Image.LANCZOS)

        img_data = img.tobytes()
        bytes_per_line = new_width * 3
        qimage = QtGui.QImage(img_data, new_width, new_height, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimage)

        if region == 1:
            x_offset = canvas.width() // 6
            canvas.image1 = pixmap
        elif region == 2:
            x_offset = canvas_width
            canvas.image2 = pixmap
        elif region == 3:
            x_offset = 2 * canvas_width
            canvas.image3 = pixmap
        canvas.scene().addPixmap(pixmap).setPos(x_offset, 0)
        canvas.scene().addText(caption, QtGui.QFont("Helvetica", 16)).setPos(x_offset + canvas_width // 2, 5)

        canvas.update()
    except Exception as e:
        print(f"Error displaying image on canvas: {str(e)}")
        print(traceback.format_exc())

def find_diameter(image, canvas, threshold_entry, offset_entry, token_entry, resolution_entry, console_text):
    try:
        diameter = None
        threshold_input = get_threshold_input(threshold_entry, offset_entry, token_entry, resolution_entry)
        image, thresh = preprocess_image(image, threshold_input)
        display_image_on_canvas(thresh, canvas, 2, "Traced")

        contours = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]

        max_p2d_contour, max_p2d_ratio = find_max_p2d_ratio_contour(contours)
        if max_p2d_contour is not None:
            diameter = calculate_diameter(max_p2d_contour)
            console_text.setText(f"Circle with Greatest Perimeter to Diameter Ratio - Diameter: {diameter}, Ratio: {max_p2d_ratio}")
            filtered_contours = [contour for contour in contours if not np.array_equal(contour, max_p2d_contour)]
            display_contours(image, filtered_contours, canvas, 2, "Traced", (0, 255, 0))
        else:
            console_text.setText("No circle with sufficient perimeter to diameter ratio found.")
        return diameter, threshold_input
    except Exception as e:
        console_text.setText(f"Error finding diameter: {str(e)}")
        print(traceback.format_exc())
        return None, None

def find_contours(image, diameter, threshold_input, canvas, console_text):
    try:
        image, thresh = preprocess_image(image, threshold_input)
        kernel_size = math.ceil(diameter / (token / offset) * 2)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        thresh = cv2.dilate(thresh, kernel)
        epsilon = kernel_size / resolution

        contours_tuple = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]
        contours = [cv2.approxPolyDP(contour, epsilon, True) for contour in contours_tuple]

        max_p2d_contour, max_p2d_ratio = find_max_p2d_ratio_contour(contours)
        filtered_contours = [contour for contour in contours if not np.array_equal(contour, max_p2d_contour)]
        display_contours(image, filtered_contours, canvas, 3, "Offset", (255, 0, 0))

        if max_p2d_contour is not None:
            diameter = calculate_diameter(max_p2d_contour)
            console_text.setText(f"Circle with Greatest Perimeter to Diameter Ratio - Diameter: {diameter}, Ratio: {max_p2d_ratio}")
        else:
            console_text.setText("No circle with sufficient perimeter to diameter ratio found.")

        return contours, image
    except Exception as e:
        console_text.setText(f"Error finding contours: {str(e)}")
        print(traceback.format_exc())
        return None, None

# ============================================================
# DXF Functions
# ============================================================
def save_dxf_file(doc, file_name, folder_name):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    design_files_directory = os.path.join(script_directory, "..", folder_name)
    os.makedirs(design_files_directory, exist_ok=True)
    output_path = os.path.join(design_files_directory, file_name + ".dxf")
    doc.saveas(output_path)
    return file_name + ".dxf"


def save_single_dxf(contour, scale_factor, pos_xy, file_name, idx, folder_name):
    center_y, center_x = pos_xy
    doc = ezdxf.new()
    msp = doc.modelspace()
    points = [
        (point[0][1] * scale_factor - center_y * scale_factor,
         point[0][0] * scale_factor - center_x * scale_factor)
        for point in contour
    ]
    if points[0] != points[-1]:
        points.append((points[0][0], points[0][1]))
    msp.add_lwpolyline(points)
    single_name = f"{file_name}_contour_{idx+1}"
    output_path = save_dxf_file(doc, single_name, folder_name)
    return output_path


def calculate_grid_size(contours, scale_factor):
    all_points = np.vstack([contour.reshape(-1, 2) for contour in contours])
    min_x, min_y = np.min(all_points, axis=0)
    max_x, max_y = np.max(all_points, axis=0)
    x_size = max_x - min_x
    y_size = max_y - min_y
    gridy_size = math.ceil(x_size / 42 * scale_factor * 25.4)
    gridx_size = math.ceil(y_size / 42 * scale_factor * 25.4)
    return gridx_size, gridy_size


def save_contours_as_dxf(contours, file_name, scale_factor, console_text, folder_name, splitDXF=False):
    try:
        max_p2d_contour, max_p2d_ratio = find_max_p2d_ratio_contour(contours)
        if max_p2d_contour is None:
            console_text.setText("No valid contours found.")
            return None, None, None

        filtered_contours = [contour for contour in contours if not np.array_equal(contour, max_p2d_contour)]
        filtered_contours = [contour for contour in filtered_contours if cv2.contourArea(contour) >= 1000]
        if not filtered_contours:
            console_text.setText("No valid contours found after filtering.")
            return None, None, None

        pos_xy = []
        for contour in filtered_contours:
            all_points = np.vstack(contour.reshape(-1, 2))
            min_x, min_y = np.min(all_points, axis=0)
            max_x, max_y = np.max(all_points, axis=0)
            center_y = round((min_x + max_x) / 2, 1)
            center_x = round((min_y + max_y) / 2, 1)
            pos_xy.append([center_x, center_y])

        # Calculate bounding box for consistent origin
        all_points = np.vstack([contour.reshape(-1, 2) for contour in filtered_contours])
        min_x, min_y = np.min(all_points, axis=0)
        max_x, max_y = np.max(all_points, axis=0)
        abs_center_x = (min_x + max_x) / 2
        abs_center_y = (min_y + max_y) / 2

        offset_pos_xy = []
        for contour in filtered_contours:
            all_points = np.vstack(contour.reshape(-1, 2))
            min_x, min_y = np.min(all_points, axis=0)
            max_x, max_y = np.max(all_points, axis=0)
            center_y = round(((min_x + max_x) / 2 - abs_center_x) * scale_factor * 25.4, 1)
            center_x = round(((min_y + max_y) / 2 - abs_center_y) * scale_factor * 25.4, 1)
            offset_pos_xy.append([center_x, center_y])

        # Save offset positions for SCAD generation
        try:
            temp_centers_path = os.path.join(os.path.dirname(__file__), '..', 'offset_pos_xy.pkl')
            with open(temp_centers_path, 'wb') as f:
                pickle.dump(offset_pos_xy, f)
        except Exception as e:
            print(f"Warning: Could not save offset_pos_xy for OpenSCAD import: {e}")

        if splitDXF:
            output_paths = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(save_single_dxf, contour, scale_factor, pos_xy[idx], file_name, idx, folder_name)
                    for idx, contour in enumerate(filtered_contours)
                ]
                for future in concurrent.futures.as_completed(futures):
                    output_paths.append(future.result())
            gridx_size, gridy_size = calculate_grid_size(filtered_contours, scale_factor)
            console_text.setText(f"Saved {len(output_paths)} DXF files: {output_paths}")
            return output_paths, gridx_size, gridy_size
        else:
            doc = ezdxf.new()
            msp = doc.modelspace()
            for contour in filtered_contours:
                points = [
                    (point[0][1] * scale_factor - center_y * scale_factor,
                     point[0][0] * scale_factor - center_x * scale_factor)
                    for point in contour
                ]
                if points[0] != points[-1]:
                    points.append((points[0][0], points[0][1]))
                msp.add_lwpolyline(points)
            output_path = save_dxf_file(doc, file_name, folder_name)
            gridx_size, gridy_size = calculate_grid_size(filtered_contours, scale_factor)
            pyperclip.copy(output_path)
            console_text.setText(
                f"File saved successfully: {output_path}\n"
                f"File path '{output_path}' copied to clipboard.\n"
                f"Grid X Size: {gridx_size}, Grid Y Size: {gridy_size}"
            )
            return output_path, gridx_size, gridy_size
    except Exception as e:
        console_text.setText(f"Error saving DXF: {str(e)}")
        print(traceback.format_exc())
        return None, None, None


def measure_dxf_bounding_box(dxf_path, folder_path, splitDXF=False):
    """Measure DXF cutout dimensions in mm. Returns 'Length x Width' string or empty."""
    try:
        if splitDXF and isinstance(dxf_path, list):
            measure_file = os.path.join(folder_path, os.path.basename(dxf_path[0]))
        else:
            measure_file = os.path.join(folder_path, os.path.basename(dxf_path))
        doc = ezdxf.readfile(measure_file)
        msp = doc.modelspace()
        pts = [p for e in msp for p in e.get_points()]
        length_mm = (max(p[0] for p in pts) - min(p[0] for p in pts)) * 25.4
        width_mm = (max(p[1] for p in pts) - min(p[1] for p in pts)) * 25.4
        return f"\nCutout: {length_mm:.1f}mm x {width_mm:.1f}mm"
    except Exception:
        return ""


def calculate_scoop_positions(dxf_path, folder_path, gridy_size, splitDXF=False):
    """Calculate Y positions for finger scoops from DXF tool outline edges."""
    scoop_y_pos = gridy_size * 42 / 2
    scoop_y_neg = gridy_size * 42 / 2
    try:
        if splitDXF and isinstance(dxf_path, list):
            measure_file = os.path.join(folder_path, os.path.basename(dxf_path[0]))
        else:
            measure_file = os.path.join(folder_path, os.path.basename(dxf_path))
        doc = ezdxf.readfile(measure_file)
        msp = doc.modelspace()
        pts = [p for e in msp for p in e.get_points()]
        scoop_y_pos = max(p[1] for p in pts) * 25.4
        scoop_y_neg = abs(min(p[1] for p in pts)) * 25.4
    except Exception:
        pass
    return scoop_y_pos, scoop_y_neg


# ============================================================
# SCAD Generation — Injection Helpers
# ============================================================
def load_scad_template():
    """Load the base SCAD template file."""
    template_path = os.path.join(os.path.dirname(__file__), "..", "Step 2 DXF to STL.scad")
    with open(template_path, 'r') as f:
        return f.read()


def inject_general_settings(scad, gridx, gridy, height=2.8, splitDXF=False):
    """Inject size, chamfer disable, and multiple_dxf flag."""
    scad = scad.replace('size = [5, 2, 6];', f'size = [{gridx}, {gridy}, {height}];')
    scad = scad.replace('multiple_dxf = false;', f'multiple_dxf = {str(splitDXF).lower()};')
    scad = scad.replace('use_chamfered_extrude = true;', 'use_chamfered_extrude = false;')
    scad = scad.replace('chamfer_height = 5;', 'chamfer_height = 3;')
    return scad


def _load_offset_positions(num_files):
    """Load contour center positions from temp pickle file."""
    try:
        temp_path = os.path.join(os.path.dirname(__file__), '..', 'offset_pos_xy.pkl')
        if os.path.exists(temp_path):
            with open(temp_path, 'rb') as f:
                pos_xy = pickle.load(f)
            if len(pos_xy) == num_files:
                return pos_xy
    except Exception:
        pass
    return [[0, 0] for _ in range(num_files)]


def inject_dxf_options(scad, dxf_path, splitDXF=False):
    """Inject DXF file paths, cut depths, positions, and section adjustments."""
    if splitDXF and isinstance(dxf_path, list):
        return _inject_dxf_split(scad, dxf_path)
    else:
        dxf_path = dxf_path.replace("\\", "/")
        return scad.replace(
            'dxf_file_path = "examples/example.dxf";',
            f'dxf_file_path = "{dxf_path}";'
        )


def _inject_dxf_split(scad, dxf_paths):
    """Handle split DXF injection for multi-contour tools."""
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
    pos_xy = _load_offset_positions(num_files)
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


def generate_border_and_text(label_text, border_color="blue", gridx=6, gridy=2):
    """Generate border/text Customizer parameters and SCAD geometry.

    Returns (params_str, geometry_str) — params go before end_of_customizer_opts,
    geometry gets appended at end of file.
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
    )
    geometry = f"""
// === Colored border around bin top edge ===
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
    rotate([0, 0, 180])
    text(text_content, size = border_text_size, font = "Arial Rounded MT Bold", halign = "center", valign = "center");
}}
"""
    return params, geometry


def inject_border_and_text(scad, label_text, border_color, gridx, gridy):
    """Inject border/text params into Customizer and append geometry.

    Params are inserted before Section Adjustments to keep Customizer order:
    General → DXF → Finger Slot → Border and Text → (rest collapsed below)
    """
    params, geometry = generate_border_and_text(label_text, border_color, gridx, gridy)
    scad = scad.replace(
        '/* [Section Adjustments] */',
        params + '\n/* [Section Adjustments] */'
    )
    scad += geometry
    return scad


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


# ============================================================
# SCAD Generation — Main Assemblers
# ============================================================
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
        global scad_file_path

        # Setup output directory
        script_directory = os.path.dirname(os.path.abspath(__file__))
        design_files_directory = os.path.join(script_directory, "..", folder_name)
        os.makedirs(design_files_directory, exist_ok=True)
        scad_file_path = os.path.join(design_files_directory, f"{file_name}.scad")

        # Build SCAD content
        scad = load_scad_template()
        scad = inject_general_settings(scad, gridx_size, gridy_size, splitDXF=splitDXF)
        scad = inject_dxf_options(scad, dxf_path, splitDXF)
        scad = inject_finger_scoops(scad, dxf_path, design_files_directory, gridy_size, splitDXF)
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
        design_files_directory = os.path.join(script_directory, "..", folder_name)
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
            f"// Margin around tool outline in mm\n"
            f"margin = 10; // [5:1:30]\n"
            f"// Slab thickness in mm\n"
            f"slab_height = 0.60; // [0.20:0.20:2.0]\n\n"
            f"linear_extrude(height = slab_height)\n"
            f"difference() {{\n"
            f"    offset(delta = margin)\n"
            f"        scale([25.4, 25.4])\n"
            f"            import(\"{dxf_files[0]}\");\n"
            f"{dxf_cuts}\n"
            f"}}\n"
        )

        with open(test_slab_path, 'w') as test_file:
            test_file.write(test_slab_content)

        dim_text = measure_dxf_bounding_box(dxf_path, design_files_directory, splitDXF)
        console_text.setText(f"Test slab written to: {os.path.basename(test_slab_path)}{dim_text}")

    except Exception as e:
        console_text.setText(f"Error generating test slab: {str(e)}")
        print(traceback.format_exc())


# ============================================================
# UI Functions
# ============================================================
def select_image(console_text, default_dir=None):
    try:
        file_dialog = QtWidgets.QFileDialog()
        start_dir = default_dir if default_dir is not None else ""
        file_path, _ = file_dialog.getOpenFileName(
            None, "Select Image", start_dir, "Image files (*.jpg;*.jpeg;*.png;*.bmp)"
        )
        if file_path:
            print(f"Selected file: {file_path}")
        else:
            print("No file selected.")
        file_name, file_extension = os.path.splitext(os.path.basename(file_path))
        return file_path, file_name
    except Exception as e:
        console_text.setText(f"Error selecting image: {str(e)}")
        print(traceback.format_exc())
        return None, None

def create_main_window():
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    canvas = ui.canvas
    canvas.setScene(QtWidgets.QGraphicsScene())

    return (MainWindow, canvas, ui.load_button, ui.process_button, ui.import_button,
            ui.exit_button, ui.threshold_entry, ui.offset_entry, ui.token_entry,
            ui.resolution_entry, ui.console_text)

def exit_application(console_text):
    try:
        global scad_file_path
        QtWidgets.QApplication.quit()
    except Exception as e:
        console_text.setText(f"Error exiting application: {str(e)}")
        print(traceback.format_exc())
