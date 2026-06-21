def get_attractions(city: str) -> list[dict]:
    """Gets popular tourist attractions and landmarks for a specified city.

    Args:
        city (str): The name of the city (e.g., "Taipei", "Taichung", "Yilan", "Kaohsiung").

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents an attraction
                    containing its name, type (Indoor/Outdoor), and description.
                    Returns an empty list if the city is unsupported.
    """
    if not isinstance(city, str):
        return []

    # Normalize input city name by stripping whitespace and capitalizing
    normalized_city = city.strip().capitalize()
    
    # Mock attractions database
    mock_attractions_db = {
        "Taipei": [
            {
                "name": "Taipei 101",
                "type": "Indoor",
                "description": "A landmark supertall skyscraper with an observatory overlooking the city."
            },
            {
                "name": "Yangmingshan National Park",
                "type": "Outdoor",
                "description": "A volcanic national park known for cherry blossoms, hot springs, and hiking trails."
            }
        ],
        "Taichung": [
            {
                "name": "National Taichung Theater",
                "type": "Indoor",
                "description": "An opera house with stunning modern architecture designed by Toyo Ito."
            },
            {
                "name": "Gaomei Wetlands",
                "type": "Outdoor",
                "description": "A scenic tidal flat known for its long boardwalk and beautiful sunset views."
            }
        ],
        "Yilan": [
            {
                "name": "Jimmy Park",
                "type": "Outdoor",
                "description": "A famous public art park themed around the works of illustrator Jimmy Liao."
            },
            {
                "name": "Lanyang Museum",
                "type": "Indoor",
                "description": "A museum showcasing local Yilan culture, history, and unique architecture."
            }
        ],
        "Kaohsiung": [
            {
                "name": "Pier-2 Art Center",
                "type": "Outdoor",
                "description": "An art center in an abandoned warehouse area filled with outdoor sculptures and murals."
            },
            {
                "name": "Fo Guang Shan Buddha Museum",
                "type": "Indoor",
                "description": "A large Buddhist museum featuring a giant bronze Buddha statue and holy relics."
            }
        ]
    }
    
    # Safely fetch the attractions list, default to empty list if unsupported
    return mock_attractions_db.get(normalized_city, [])

if __name__ == "__main__":
    print("=== Testing Attraction Tool ===")
    
    # 1. Test supported city (Yilan)
    print("Yilan attractions:")
    yilan_attractions = get_attractions("Yilan")
    for attr in yilan_attractions:
        print(f"- {attr['name']} ({attr['type']}): {attr['description']}")
    print()
    
    # 2. Test case sensitivity and spacing normalization
    print("Query '  taipei  ':")
    taipei_attractions = get_attractions("  taipei  ")
    for attr in taipei_attractions:
        print(f"- {attr['name']} ({attr['type']}): {attr['description']}")
    print()
    
    # 3. Test unsupported city (should return empty list)
    print("Tainan (unsupported) attractions:")
    print(get_attractions("Tainan"))
