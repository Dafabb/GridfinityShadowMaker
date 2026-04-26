"""Shared utility functions for GSM."""
import os
import traceback
from PyQt5 import QtWidgets, QtGui
from src.ui import Ui_MainWindow  # type: ignore


scad_file_path = None


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
