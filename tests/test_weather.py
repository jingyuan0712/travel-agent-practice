from unittest.mock import patch, MagicMock
import pytest
import requests
from tools.weather_tool import get_weather

def test_weather_success():
    """Verifies that get_weather returns parsed weather variables (temperature, rain_probability, weather description) 
    successfully when coordinates match and Open-Meteo returns a 200 response with the correct schema."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current": {
                "temperature_2m": 27.2,
                "weather_code": 0,  # Sunny
                "time": "2026-07-02T15:30"
            },
            "hourly": {
                "time": [
                    "2026-07-02T14:00",
                    "2026-07-02T15:00",
                    "2026-07-02T16:00"
                ],
                "precipitation_probability": [0, 10, 20]
            }
        }
        mock_get.return_value = mock_response
        
        res = get_weather("Taipei")
        assert res["city"] == "Taipei"
        assert res["temperature"] == 27
        assert res["weather"] == "Sunny"
        assert res["rain_probability"] == 10  # Matches target hour (15:00)

def test_weather_unsupported_city():
    """Verifies that a ValueError is raised when querying a city name that is not supported in coordinate mappings."""
    with pytest.raises(ValueError) as excinfo:
        get_weather("Tainan")
    assert "Unsupported city" in str(excinfo.value)

def test_weather_invalid_type():
    """Verifies that a ValueError is raised when a parameter of invalid type (non-string) is supplied."""
    with pytest.raises(ValueError) as excinfo:
        get_weather(123)
    assert "must be a string" in str(excinfo.value)

def test_weather_api_failure():
    """Verifies that a RuntimeError is raised if the Open-Meteo API requests fail with non-200 status codes."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Internal Server Error")
        mock_get.return_value = mock_response
        
        with pytest.raises(RuntimeError) as excinfo:
            get_weather("Taipei")
        assert "Failed to retrieve weather data" in str(excinfo.value)
