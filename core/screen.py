#!/usr/bin/env python3
"""
core/screen.py — KENWAY Screen Reader
Captures the screen and extracts text via OCR (tesseract).
"""

import logging
import mss
import pytesseract
from PIL import Image

log = logging.getLogger("kenway.screen")


def read_screen(region: dict = None) -> str:
    """
    Capture the full screen (or a region) and return OCR text.
    region: {"top": y, "left": x, "width": w, "height": h} or None for full screen.
    """
    try:
        with mss.mss() as sct:
            monitor = region if region else sct.monitors[1]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        # Tesseract config: fast mode, English
        config = "--oem 3 --psm 6"
        text = pytesseract.image_to_string(img, config=config)
        cleaned = " ".join(text.split())
        log.info(f"Screen read: {len(cleaned)} chars")
        return cleaned

    except Exception as e:
        log.error(f"Screen read error: {e}")
        return "Could not read screen."


def find_text_location(search_text: str) -> tuple:
    """
    Find the pixel location of specific text on screen.
    Returns (x, y) center of the found text, or (None, None).
    """
    try:
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        for i, word in enumerate(data["text"]):
            if search_text.lower() in word.lower() and int(data["conf"][i]) > 60:
                x = data["left"][i] + data["width"][i] // 2
                y = data["top"][i] + data["height"][i] // 2
                log.info(f"Found '{search_text}' at ({x}, {y})")
                return (x, y)

    except Exception as e:
        log.error(f"find_text_location error: {e}")

    return (None, None)
