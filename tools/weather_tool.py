import requests

def get_weather(city: str) -> dict:
    """Gets real-time weather information for a specified city using Open-Meteo API.

    Args:
        city (str): The name of the city (e.g., "Taipei", "Taichung", "Yilan", "Kaohsiung").

    Returns:
        dict: A dictionary containing the city name, temperature (Celsius), 
              rain probability (percentage), and weather description.

    Raises:
        ValueError: If the input city is not supported by the coordinates map.
        RuntimeError: If the HTTP request to Open-Meteo fails.
    """
    # 1. Validate and normalize input city name
    if not isinstance(city, str):
        raise ValueError("City parameter must be a string.")
        
    normalized_city = city.strip().capitalize()

    # 2. City-to-coordinate mapping for the 4 supported cities
    city_coordinates = {
        "Taipei": {"latitude": 25.0330, "longitude": 121.5654},
        "Yilan": {"latitude": 24.7570, "longitude": 121.7530},
        "Taichung": {"latitude": 24.1469, "longitude": 120.6839},
        "Kaohsiung": {"latitude": 22.6150, "longitude": 120.2975}
    }

    if normalized_city not in city_coordinates:
        supported_cities = ", ".join(city_coordinates.keys())
        raise ValueError(
            f"Unsupported city: '{city}'. Supported cities are: {supported_cities}."
        )

    coords = city_coordinates[normalized_city]
    
    # 3. Construct API URL and request parameters (No API key required)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "current": "temperature_2m,weather_code",
        "hourly": "precipitation_probability",
        "forecast_days": 1,
        "timezone": "auto"
    }

    try:
        # 4. Make HTTP GET request
        response = requests.get(url, params=params, timeout=10)
        
        # 5. Handle HTTP errors (e.g., status codes 4xx, 5xx)
        response.raise_for_status()
        
        # 6. Parse response JSON
        data = response.json()
        
        # Extract current weather conditions
        current_data = data.get("current", {})
        temp = current_data.get("temperature_2m")
        weather_code = current_data.get("weather_code")
        current_time = current_data.get("time")  # Format: "YYYY-MM-DDTHH:MM"

        # Extract hourly forecast to match current hour precipitation probability
        hourly_data = data.get("hourly", {})
        hourly_times = hourly_data.get("time", [])
        hourly_probs = hourly_data.get("precipitation_probability", [])
        
        # Convert "2026-06-21T14:30" -> "2026-06-21T14:00" to match hourly timeline indexes
        rain_probability = 0
        if current_time and hourly_times and hourly_probs:
            target_hour_str = current_time[:13] + ":00"
            if target_hour_str in hourly_times:
                hour_index = hourly_times.index(target_hour_str)
                rain_probability = hourly_probs[hour_index]
            else:
                # Default fallback if the matching index is missing
                rain_probability = hourly_probs[0]

        # 7. Convert WMO weather code to descriptive string
        weather_desc = _parse_weather_code(weather_code)

        # 8. Return formatted output dictionary
        return {
            "city": normalized_city,
            "temperature": round(temp) if temp is not None else None,
            "weather": weather_desc,
            "rain_probability": rain_probability
        }

    except requests.RequestException as e:
        # 9. Handle request failures (connection loss, timeouts, DNS resolution errors)
        raise RuntimeError(f"Failed to retrieve weather data from Open-Meteo API: {e}")

def _parse_weather_code(code: int) -> str:
    """Helper to convert WMO weather interpretation code to description."""
    if code is None:
        return "Unknown"
    
    # Mapping based on WMO standards:
    # 0: Clear sky -> Sunny
    # 1, 2: Mainly clear, partly cloudy -> Mostly Sunny
    # 3: Overcast -> Cloudy
    # 45, 48: Fog -> Foggy
    # 51-57: Drizzle -> Rainy
    # 61-67, 80-82: Rain -> Rainy
    # 71-77, 85-86: Snow -> Snowy
    # 95-99: Thunderstorm -> Thunderstorm
    if code == 0:
        return "Sunny"
    elif code in [1, 2]:
        return "Mostly Sunny"
    elif code == 3:
        return "Cloudy"
    elif code in [45, 48]:
        return "Foggy"
    elif code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return "Rainy"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "Snowy"
    elif code in [95, 96, 99]:
        return "Thunderstorm"
    else:
        return "Unknown"

if __name__ == "__main__":
    # Test section to verify integration works
    print("=== Testing Real Weather Tool (Open-Meteo API) ===")
    
    # Test Yilan
    try:
        print("Yilan Weather:")
        print(get_weather("Yilan"))
    except Exception as e:
        print(f"Error: {e}")
        
    print()
    
    # Test Taipei
    try:
        print("Taipei Weather:")
        print(get_weather("Taipei"))
    except Exception as e:
        print(f"Error: {e}")
