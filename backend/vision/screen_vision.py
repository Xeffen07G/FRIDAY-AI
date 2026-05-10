import pyautogui
import cv2
import pytesseract
import numpy as np
from PIL import Image

class ScreenVision:
    """Handles capturing the screen and extracting text/UI elements."""
    
    def __init__(self):
        # Configure Tesseract path if necessary (especially on Windows)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
        
    def capture_screen(self, save_path="screenshot.png"):
        """Takes a screenshot and saves it to disk."""
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        return save_path
        
    def ocr_screen(self, image_path="screenshot.png") -> str:
        """Extracts text from an image using pytesseract."""
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            return f"OCR Error: {str(e)}"
            
    def analyze_ui(self, image_path="screenshot.png"):
        """Basic OpenCV analysis to find buttons or elements (Placeholder for advanced CV)."""
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            return f"Found {len(contours)} potential UI elements."
        except Exception as e:
            return f"Vision Error: {str(e)}"
