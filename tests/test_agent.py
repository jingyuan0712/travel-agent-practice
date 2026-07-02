from unittest.mock import patch
import os
import pytest
from agents.travel_agent import TravelAgent

def test_agent_initialization():
    """Verifies that TravelAgent instantiates successfully, initializes tools structure list, 
    and sets up default models properties when API keys are configured."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "dummy_groq_key"}):
        agent = TravelAgent()
        assert agent.model_name == "llama-3.3-70b-versatile"
        assert isinstance(agent.tools, list)
        assert len(agent.tools) == 4

def test_agent_minimum_budget_calculations():
    """Verifies that TravelAgent correctly computes minimum baseline travel expenses 
    for food, transit, and lodging based on days and traveler count inputs."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "dummy_groq_key"}):
        agent = TravelAgent()
        
        # 1. 2 Days, 1 Traveler: food(600*2) + transit(200*2) + lodging(1500*1) = 3100
        cost_2_1 = agent.calculate_minimum_budget(days=2, travelers=1)
        assert cost_2_1 == 3100
        
        # 2. 3 Days, 2 Travelers: food(600*3*2) + transit(200*3*2) + lodging(1500*2) = 7800
        cost_3_2 = agent.calculate_minimum_budget(days=3, travelers=2)
        assert cost_3_2 == 7800

def test_agent_budget_attraction_filter():
    """Verifies that the agent correctly filters attractions list when the budget is set, 
    matching attraction estimated costs against the calculated remaining allowance."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "dummy_groq_key"}):
        agent = TravelAgent()
        
        # Scenario: Days=2, Travelers=1 (Base: 3100), Budget limit=3200 (Allowance = 100 for attractions)
        agent.session_memory.update_memory(days=2, travelers=1, budget=3200)
        
        attractions = [
            {"name": "Elephant Mountain", "estimated_cost": 0},
            {"name": "Paid Landmark", "estimated_cost": 80},
            {"name": "Expensive Tour", "estimated_cost": 250}
        ]
        
        filtered = agent._apply_budget_filter(attractions)
        assert len(filtered) == 2
        assert filtered[0]["name"] == "Elephant Mountain"
        assert filtered[1]["name"] == "Paid Landmark"
