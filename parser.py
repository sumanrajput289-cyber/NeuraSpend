# -*- coding: utf-8 -*-
"""
Intelligent Enterprise Expense Management & Analytics System
Academic Final Year Project - NLP Parser Engine Module
"""

import re

# Category-specific structural keyword dictionaries
CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "food", "restaurant", "lunch", "breakfast", "dinner", "cafe", 
        "pizza", "burger", "grocery", "groceries", "tea", "coffee", 
        "dining", "starbucks", "hotel", "snack", "snacks", "drinks"
    ],
    "Electronics & Gadgets": [
        "mobile", "phone", "laptop", "headphones", "keyboard", "monitor", 
        "charger", "electronics", "computer", "mouse", "ipad", "gadgets", 
        "accessories", "tablet", "screen", "cable", "software"
    ],
    "Travel & Transport": [
        "cab", "taxi", "bus", "flight", "fuel", "metro", "train", 
        "petrol", "diesel", "travel", "transport", "uber", "lyft", 
        "fare", "ticket", "subway", "airline", "commute", "parking"
    ],
    "Entertainment": [
        "movie", "game", "music", "concert", "streaming", "netflix", 
        "cinema", "theatre", "show", "ticket", "sports", "fun", 
        "clubbing", "party", "recreation", "subscription"
    ]
}

DEFAULT_CATEGORY = "Others"


def parse_transaction_text(input_text):
    """
    Analyzes raw text using deterministic regular expressions and keyword dictionaries.
    Extracts the numerical amount, isolates the description, and categorizes the transaction.
    
    Returns a dictionary:
    {
        "amount": float or 0.0,
        "category": str,
        "title": str
    }
    """
    if not input_text:
        return {"amount": 0.0, "category": DEFAULT_CATEGORY, "title": ""}

    cleaned_text = input_text.strip().lower()
    
    # 1. Processing transaction numerical amount extraction via regex
    # Matches values like 450, 2500, 30.50, ₹1000, $500, 3,500
    amount_pattern = r"(?:(?:rs\.?|inr|₹|\$|usd|eur|€|£|amount|spent|cost|of)\s*)?(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)"
    amounts_found = re.findall(amount_pattern, cleaned_text)
    
    amount = 0.0
    amount_str = ""
    
    # Filter out empty strings and locate the most plausible transactional value
    if amounts_found:
        for val in amounts_found:
            val_clean = val.replace(",", "")
            try:
                temp_val = float(val_clean)
                if temp_val > 0:
                    amount = temp_val
                    amount_str = val
                    break
            except ValueError:
                continue

    # 2. Extracting textual description / transaction title
    # We clean up auxiliary words to leave a clean title (e.g. "spent 450 on dinner" -> "dinner")
    title_text = input_text
    if amount_str:
        # Strip out the exact numerical amount from the raw text
        title_text = re.sub(re.escape(amount_str), "", title_text, flags=re.IGNORECASE)
    
    # Remove filler transition words
    stop_words = ["spent", "purchased", "for", "cost", "on", "rs", "inr", "usd", "amount", "rupees", "dollars", "of", "paid", "bought"]
    for word in stop_words:
        title_text = re.sub(rf"\b{word}\b", "", title_text, flags=re.IGNORECASE)
        
    title_text = re.sub(r"\s+", " ", title_text).strip()
    
    # Clean up punctuation and capitalize for neat database display
    title_text = title_text.strip(",.?!:;- ")
    if title_text:
        # Capitalize first character
        title_text = title_text[0].upper() + title_text[1:]
    else:
        title_text = f"Expense for {amount}" if amount > 0 else "New Expense"

    # 3. Compiling category recognition patterns by scanning keyword dictionaries
    matched_category = DEFAULT_CATEGORY
    found = False
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            # Match word boundary to avoid partial matching (e.g., matching 'bus' in 'business')
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, cleaned_text):
                matched_category = category
                found = True
                break
        if found:
            break

    # Processing transaction aggregation results
    return {
        "amount": amount,
        "category": matched_category,
        "title": title_text
    }
