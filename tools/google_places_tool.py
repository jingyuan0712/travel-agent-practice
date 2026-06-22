import os
import requests
from tools.attraction_tool import get_attractions

def get_google_places(city: str) -> list[dict]:
    """Gets tourist attractions for a city using Google Places API.
    If the API call fails or GOOGLE_PLACES_API_KEY is not set, 
    falls back to the local database get_attractions().
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("[Google Places Tool] GOOGLE_PLACES_API_KEY is not set. Falling back to local database.")
        return _fallback_to_local(city)
        
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"attractions in {city}",
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"[Google Places Tool] API request failed with status code {response.status_code}. Falling back.")
            return _fallback_to_local(city)
            
        data = response.json()
        status = data.get("status")
        if status != "OK":
            print(f"[Google Places Tool] API returned status {status}. Falling back.")
            return _fallback_to_local(city)
            
        results = data.get("results", [])[:10]
        places = []
        for r in results:
            places.append({
                "name": r.get("name"),
                "rating": r.get("rating", 0.0),
                "user_ratings_total": r.get("user_ratings_total", 0),
                "address": r.get("formatted_address", ""),
                "types": r.get("types", [])
            })
        return places
        
    except Exception as e:
        print(f"[Google Places Tool] Exception occurred: {e}. Falling back.")
        return _fallback_to_local(city)

def _fallback_to_local(city: str) -> list[dict]:
    """Helper to fetch local attractions and convert them to the Google Places schema."""
    local_attrs = get_attractions(city)
    places = []
    for attr in local_attrs:
        places.append({
            "name": attr.get("name"),
            "rating": 4.5,
            "user_ratings_total": 1000,
            "address": f"{city}, Taiwan",
            "types": [attr.get("category", "Sightseeing").lower()]
        })
    return places

if __name__ == "__main__":
    # Simple manual test
    import sys
    sys.path.append(".")
    print("Testing get_google_places fallback for Taipei:")
    res = get_google_places("Taipei")
    print(f"Returned {len(res)} places. First one:")
    if res:
        print(res[0])
