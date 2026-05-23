# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - Optical Character Recognition Receipt Scanner
"""

import re
import os
import logging

# Conditional import of Pillow and pytesseract to prevent startup failure
OCR_SUPPORTED = False
try:
    from PIL import Image
    import pytesseract
    OCR_SUPPORTED = True
except ImportError:
    logging.warning("PIL or pytesseract libraries missing from python environment.")


def execute_receipt_ocr(image_path):
    """
    Opens an image file using Pillow, processes text using Tesseract OCR,
    and attempts to parse the merchant name and total amount using regex.
    
    Returns a dictionary:
    {
        "success": bool,
        "text": str,
        "amount": float,
        "merchant": str,
        "error": str
    }
    """
    if not OCR_SUPPORTED:
        return {
            "success": False,
            "text": "",
            "amount": 0.0,
            "merchant": "",
            "error": "OCR scanning libraries (Pillow/pytesseract) are not installed."
        }

    if not os.path.exists(image_path):
        return {
            "success": False,
            "text": "",
            "amount": 0.0,
            "merchant": "",
            "error": "Target image file does not exist on disk."
        }

    try:
        # 1. Opening physical image file
        img = Image.open(image_path)

        # 2. Extracting textual records via Tesseract OCR
        # We wrap this in a strict try block in case the Tesseract binary is missing from PATH
        try:
            raw_text = pytesseract.image_to_string(img)
        except Exception as ocr_binary_err:
            logging.error("Tesseract execution failed: %s", str(ocr_binary_err))
            return {
                "success": False,
                "text": "",
                "amount": 0.0,
                "merchant": "",
                "error": "Tesseract OCR binary not found. Please install Tesseract-OCR software on your OS."
            }

        if not raw_text.strip():
            return {
                "success": True,
                "text": "",
                "amount": 0.0,
                "merchant": "",
                "error": "OCR scan completed, but no text characters were detected in image."
            }

        # 3. Processing extracted transaction parameters (Amount, Merchant)
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        
        # Heuristics: Merchant name is usually on the first non-empty line
        merchant = "N/A"
        if lines:
            # Clean up punctuation and set first line
            merchant = lines[0].strip(" ,.-_#*")
            if len(merchant) > 30:
                merchant = merchant[:27] + "..."

        # Parsing total amount using robust keyword-regex lookups
        amount = 0.0
        amount_patterns = [
            r"(?i)(?:total|amount|due|sum|net|pay|to\s*pay|paid|rs\.?|inr|₹|\$)\s*[:\s]*(\d+(?:\.\d{2})?)",
            r"(?i)(?:\bgrand\s*total\b)\s*[:\s]*(\d+(?:\.\d{2})?)",
            r"\b(\d+(?:\.\d{2}))\b"  # Fallback: scan for any decimal format numbers
        ]

        found_amount = False
        for pattern in amount_patterns:
            matches = re.findall(pattern, raw_text)
            if matches:
                # Iterate matches to find the largest plausible transaction amount
                plausible_amounts = []
                for val in matches:
                    try:
                        amt_val = float(val)
                        if amt_val > 0:
                            plausible_amounts.append(amt_val)
                    except ValueError:
                        continue
                if plausible_amounts:
                    # In receipts, the "Total" is typically the largest number
                    amount = max(plausible_amounts)
                    found_amount = True
                    break

        return {
            "success": True,
            "text": raw_text,
            "amount": amount,
            "merchant": merchant,
            "error": ""
        }

    except Exception as generic_err:
        logging.error("OCR scanner crashed: %s", str(generic_err))
        return {
            "success": False,
            "text": "",
            "amount": 0.0,
            "merchant": "",
            "error": f"OCR processing failed: {str(generic_err)}"
        }
