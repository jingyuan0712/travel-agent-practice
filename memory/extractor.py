import re

def extract_travel_info(message: str) -> dict:
    """Extracts travel details (city, days, style, budget, travelers) from a user message using regex and keywords.

    Args:
        message (str): The user input message.

    Returns:
        dict: A dictionary containing only the fields that were successfully detected.
    """
    detected = {}
    message_lower = message.lower()

    # 1. Destination City Extraction (Taipei, Yilan, Taichung, Kaohsiung)
    city_match = re.search(r"\b(taipei|yilan|taichung|kaohsiung)\b", message_lower)
    if city_match:
        detected["city"] = city_match.group(1).capitalize()

    # 2. Trip Duration Extraction (e.g., 2-day, 2 days, 3 days)
    days_match = re.search(r"\b(\d+)\s*(?:-| )days?\b", message_lower)
    if days_match:
        detected["days"] = int(days_match.group(1))

    # 3. Budget Extraction (e.g., NT$20000, Budget: 5000, Budget: NT$5000)
    budget_match = re.search(r"(?:budget|nt\$)\s*(?::| )?\s*(\d+)", message_lower)
    if budget_match:
        detected["budget"] = int(budget_match.group(1))

    # 4. Traveler Count Extraction (e.g., Travelers: 4, 4 travelers, 2 people)
    traveler_match = re.search(
        r"(?:travelers|people|pax)\s*:\s*(\d+)|\b(\d+)\s*(?:travelers|people|pax|person|persons)\b",
        message_lower
    )
    if traveler_match:
        count = traveler_match.group(1) or traveler_match.group(2)
        if count:
            detected["travelers"] = int(count)

    # 5. Travel Style Extraction
    style_match = re.search(r"(?:style|preferences?)\s*:\s*([\w\s]+)", message_lower)
    if style_match:
        detected["style"] = style_match.group(1).strip().title()
    else:
        # Fallback: scan for common style keywords inside the message (excluding 'budget' initially)
        style_keywords = ["luxury", "nature", "foodie", "local food", "adventure", "relaxation"]
        for keyword in style_keywords:
            if re.search(r"\b" + re.escape(keyword) + r"\b", message_lower):
                detected["style"] = keyword.title()
                break
        
        # Only match "budget" as a style if it is not detailing a numerical budget amount (e.g., 'budget: 5000')
        if "style" not in detected:
            if "budget" in message_lower:
                is_budget_val = re.search(r"budget\s*(?::|of|is)?\s*(?:nt\$)?\s*\d+", message_lower)
                if not is_budget_val:
                    detected["style"] = "Budget"

    return detected

if __name__ == "__main__":
    # Test cases to verify the extractor
    print("=== Testing Travel Extractor ===")
    
    test_cases = [
        "Plan a luxury 2-day trip to Taipei",
        "Budget: NT$20000",
        "Travelers: 4",
        "I want to travel to Yilan this weekend for a 3 days trip.",
        "We are 2 people planning a budget style trip to Kaohsiung.",
        "Travel Style: local food",
    ]
    
    for case in test_cases:
        print(f"Input:  '{case}'")
        print(f"Output: {extract_travel_info(case)}")
        print("-" * 40)
