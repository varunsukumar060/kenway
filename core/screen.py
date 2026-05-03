#!/usr/bin/env python3
"""
core/screen.py — KENWAY Screen Reader
Captures the active screen region and extracts text via OCR (pytesseract).
"""

import logging
import os

log = logging.getLogger("kenway.screen")


def read_screen() -> str:
    """
    Take a screenshot of the full screen, run OCR, return cleaned text.
    Speaks back a summary of what's on screen.
    """
    try:
        import mss
        import pytesseract
        from PIL import Image
        import tempfile

        with mss.mss() as sct:
            # Capture primary monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            # Save to temp file
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=tmp.name)
            tmp.close()

        # OCR
        img  = Image.open(tmp.name)
        text = pytesseract.image_to_string(img).strip()
        os.unlink(tmp.name)

        if not text:
            return "I couldn't read any text from the screen."

        # Return first 400 chars — enough for a voice summary
        summary = text[:400].replace("\n", " ").strip()
        word_count = len(text.split())
        log.info(f"Screen OCR: {word_count} words extracted.")
        return f"I can see approximately {word_count} words on screen. Here's what I read: {summary}"

    except ImportError as e:
        return f"Screen reader requires mss and pytesseract. Missing: {e}"
    except Exception as e:
        log.error(f"Screen read error: {e}")
        return f"Screen reading failed: {e}"


def capture_region(x: int, y: int, w: int, h: int) -> str:
    """Capture and OCR a specific screen region."""
    try:
        import mss
        import pytesseract
        from PIL import Image
        import tempfile

        with mss.mss() as sct:
            region = {"left": x, "top": y, "width": w, "height": h}
            shot = sct.grab(region)
            tmp  = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            mss.tools.to_png(shot.rgb, shot.size, output=tmp.name)
            tmp.close()

        text = pytesseract.image_to_string(Image.open(tmp.name)).strip()
        os.unlink(tmp.name)
        return text or "No text found in that region."

    except Exception as e:
        log.error(f"Region capture error: {e}")
        return f"Region capture failed: {e}"
