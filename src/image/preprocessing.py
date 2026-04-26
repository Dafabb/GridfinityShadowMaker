"""Image preprocessing, contour detection, and diameter finding."""
import cv2
import numpy as np
import math
import traceback
from src.image.display import display_image_on_canvas, display_contours
from src.utils import get_threshold_input
import src.utils as _utils


def preprocess_image(image, threshold_input):
    if isinstance(image, str):
        image = cv2.imread(image)
    imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(imgray, threshold_input, 255, cv2.THRESH_BINARY)
    thresh = cv2.bitwise_not(thresh)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    return image, thresh


def calculate_diameter(contour):
    (x, y), radius = cv2.minEnclosingCircle(contour)
    return 2 * radius


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
        kernel_size = math.ceil(diameter / (_utils.token / _utils.offset) * 2)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        thresh = cv2.dilate(thresh, kernel)
        epsilon = kernel_size / _utils.resolution

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
