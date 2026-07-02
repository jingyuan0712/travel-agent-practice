import pytest
from memory.session_memory import SessionMemory
from memory.extractor import extract_travel_info

def test_session_memory_operations():
    """Verifies that SessionMemory initializes empty, merges parameter updates, handles integer 
    type coercions for keys like days/budget/travelers, and clears storage correctly."""
    mem = SessionMemory()
    
    # 1. Default empty check
    state = mem.get_memory()
    assert state["city"] is None
    assert state["days"] is None
    assert state["budget"] is None
    
    # 2. Update properties
    mem.update_memory(city="Taipei", budget=3200)
    state = mem.get_memory()
    assert state["city"] == "Taipei"
    assert state["budget"] == 3200
    
    # 3. Numeric string conversion check
    mem.update_memory(days="2", travelers="1")
    state = mem.get_memory()
    assert state["days"] == 2
    assert state["travelers"] == 1
    
    # 4. Memory resets check
    mem.clear_memory()
    state = mem.get_memory()
    assert state["city"] is None
    assert state["days"] is None

def test_extractor_regex_matching():
    """Verifies that extract_travel_info uses regular expressions to correctly extract parameters 
    like destination city, trip duration, budgets, style, and traveler count from dialogue strings."""
    # Test case 1: Standard query
    res = extract_travel_info("Plan a 2-day trip to Taipei. Budget: NT$3200.")
    assert res.get("city") == "Taipei"
    assert res.get("days") == 2
    assert res.get("budget") == 3200
    
    # Test case 2: Style and travelers query
    res = extract_travel_info("We are 3 travelers planning a nature style trip to Yilan.")
    assert res.get("city") == "Yilan"
    assert res.get("travelers") == 3
    assert res.get("style") == "Nature"  # Scans and matches 'nature'
