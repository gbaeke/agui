"""Weather tool for getting current weather information."""

import json
import httpx
from agent_framework import ai_function

from utils import logger


@ai_function(description="Get the current weather for a location")
def get_weather(location: str) -> str:
    """Get real weather information for a location using Open-Meteo API."""
    try:
        # Step 1: Geocode the location to get coordinates
        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        geocode_params = {"name": location, "count": 1, "language": "en", "format": "json"}
        
        with httpx.Client(timeout=10.0) as client:
            geo_response = client.get(geocode_url, params=geocode_params)
            geo_data = geo_response.json()
            
            if "results" not in geo_data or len(geo_data["results"]) == 0:
                return json.dumps({"error": f"Location '{location}' not found"})
            
            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            resolved_name = result.get("name", location)
            country = result.get("country", "")
            
            # Step 2: Get current weather
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            }
            
            weather_response = client.get(weather_url, params=weather_params)
            weather_data = weather_response.json()
            
            current = weather_data.get("current", {})
            
            # Map weather codes to conditions
            weather_code = current.get("weather_code", 0)
            condition = _weather_code_to_condition(weather_code)
            
            return json.dumps({
                "location": f"{resolved_name}, {country}".strip(", "),
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "condition": condition,
            })
            
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return json.dumps({"error": str(e)})


def _weather_code_to_condition(code: int) -> str:
    """Map WMO weather codes to simple condition strings."""
    if code == 0:
        return "sunny"
    elif code in (1, 2):
        return "partly cloudy"
    elif code == 3:
        return "cloudy"
    elif code in (45, 48):
        return "foggy"
    elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rainy"
    elif code in (71, 73, 75, 77, 85, 86):
        return "snowy"
    elif code in (95, 96, 99):
        return "stormy"
    else:
        return "cloudy"
