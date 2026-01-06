# routes/services/weather.py
import os
import requests
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather_risk(lat, lon):
    """
    Returns weather information and a simple road risk level
    based on OpenWeatherMap data.
    
    Risk Levels:
    - high: Rain, Snow, Thunderstorm
    - medium: Fog, Mist, strong wind (>10 m/s)
    - low: Otherwise
    """
    if not OPENWEATHER_API_KEY:
        return {"error": "No API key set. Please add OPENWEATHER_API_KEY to .env"}

    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()

        # Extract relevant info
        weather_main = data['weather'][0]['main'].lower()
        weather_desc = data['weather'][0]['description']
        temp = data['main']['temp']
        wind_speed = data['wind']['speed']

        # Determine risk
        if "rain" in weather_main or "snow" in weather_main or "thunderstorm" in weather_main:
            risk = "high"
        elif "fog" in weather_main or "mist" in weather_main or wind_speed > 10:
            risk = "medium"
        else:
            risk = "low"

        return {
            "weather": weather_desc,
            "temperature": temp,
            "wind_speed": wind_speed,
            "risk": risk
        }

    except requests.exceptions.HTTPError as e:
        return {"error": "API request failed", "details": str(e)}
    except requests.exceptions.RequestException as e:
        return {"error": "Network error or timeout", "details": str(e)}
    except KeyError:
        return {"error": "Unexpected API response structure", "data": data}
