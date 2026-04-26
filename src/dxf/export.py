"""DXF file export functions."""
import os
import math
import pickle
import traceback
import concurrent.futures
import cv2
import numpy as np
import ezdxf
import pyperclip
from src.image.preprocessing import find_max_p2d_ratio_contour


def load_offset_positions(num_files):
    """Load contour center positions from temp pickle file."""
    try:
        temp_path = os.path.join(os.path.dirname(__file__), '..', '..', 'offset_pos_xy.pkl')
        if os.path.exists(temp_path):
            with open(temp_path, 'rb') as f:
                pos_xy = pickle.load(f)
            if len(pos_xy) == num_files:
                return pos_xy
    except Exception:
        pass
    return [[0, 0] for _ in range(num_files)]


def save_dxf_file(doc, file_name, folder_name):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    design_files_directory = os.path.join(script_directory, "..", "..", folder_name)
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
            temp_centers_path = os.path.join(os.path.dirname(__file__), '..', '..', 'offset_pos_xy.pkl')
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
