"""Canvas display and image rendering helpers."""
import cv2
import traceback
from PIL import Image
from PyQt5 import QtGui


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


def display_contours(image, contours, canvas, region, caption, color):
    contours_img = image.copy()
    thickness = max(1, min(image.shape[0], image.shape[1]) // 200)
    cv2.drawContours(contours_img, contours, -1, color, thickness)
    display_image_on_canvas(contours_img, canvas, region, caption)
