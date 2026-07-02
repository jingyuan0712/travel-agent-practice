from unittest.mock import patch, MagicMock
import os
import pytest
from tools.google_places_tool import get_google_places

def test_places_fallback_when_no_api_key():
    """Verifies that the Google Places tool automatically falls back to local database attractions 
    when GOOGLE_PLACES_API_KEY is not set in the environment variables."""
    with patch.dict(os.environ, {}, clear=True):
        res = get_google_places("Taipei")
        assert isinstance(res, list)
        assert len(res) == 10  # Fallback yields 10 local database attractions
        assert res[0]["name"] == "Taipei 101"
        assert res[0]["rating"] == 4.5
        assert "tourist_attraction" not in res[0]["types"]  # Fallback uses categories as types

def test_places_mock_api_success():
    """Verifies that the API fetches, filters, and maps response structures successfully when 
    a valid key is present and the Google Places HTTP requests return successfully."""
    with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "dummy_places_key"}):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "OK",
                "results": [
                    {
                        "name": "Observatory deck",
                        "rating": 4.7,
                        "user_ratings_total": 2400,
                        "formatted_address": "Xinyi District, Taipei",
                        "types": ["observatory", "landmark"]
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            res = get_google_places("Taipei")
            assert len(res) == 1
            assert res[0]["name"] == "Observatory deck"
            assert res[0]["rating"] == 4.7
            assert res[0]["user_ratings_total"] == 2400
            assert res[0]["address"] == "Xinyi District, Taipei"
            assert "observatory" in res[0]["types"]

def test_places_api_non_ok_status_fallback():
    """Verifies that when the Google Places Text Search API returns a non-OK status (e.g. REQUEST_DENIED), 
    the tool catches it and gracefully falls back to local attractions database."""
    with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "dummy_places_key"}):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "REQUEST_DENIED",
                "results": []
            }
            mock_get.return_value = mock_response
            
            res = get_google_places("Taipei")
            assert isinstance(res, list)
            assert len(res) > 0  # Falls back to local database
            assert res[0]["name"] == "Taipei 101"
