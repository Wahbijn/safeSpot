from django.http import JsonResponse
from django.shortcuts import render
from .services.osrm import get_route
from .services.weather import get_weather_risk
from .services.alerts import generate_alerts
from datetime import datetime
import requests
from django.conf import settings
import os
import csv
import json

def get_current_weather_for_routes(city="Tunis"):
    """Fetch current weather for route safety calculation"""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return None

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            'temp': round(data['main']['temp'], 1),
            'humidity': data['main']['humidity'],
            'weather': data['weather'][0]['main'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'wind_speed': round(data['wind']['speed'], 1),
            'weather_id': data['weather'][0]['id']
        }
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

def get_city_routes_data():
    """Get real city data with coordinates and accident information for routes"""
    csv_path = os.path.join(settings.BASE_DIR, "..", "data", "accidents_city_detail.csv")
    city_data = {}

    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            row_count = 0
            for row in reader:
                try:
                    city = (row.get("City") or "").strip()
                    state = (row.get("State") or "").strip()
                    lat = float(row.get("Start_Lat", 0))
                    lng = float(row.get("Start_Lng", 0))
                    accidents = int(row.get("Total Accidents", 0))
                    severity = int(row.get("Severity", 2))

                    if not city or not state:
                        continue

                    city_key = f"{city}, {state}"

                    # Aggregate by city
                    if city_key not in city_data:
                        city_data[city_key] = {
                            'city': city,
                            'state': state,
                            'lat': lat,
                            'lng': lng,
                            'total_accidents': 0,
                            'severity_sum': 0,
                            'count': 0
                        }

                    city_data[city_key]['total_accidents'] += accidents
                    city_data[city_key]['severity_sum'] += (severity * accidents)
                    city_data[city_key]['count'] += 1

                    # Average coordinates for better centering
                    city_data[city_key]['lat'] = (city_data[city_key]['lat'] * (city_data[city_key]['count'] - 1) + lat) / city_data[city_key]['count']
                    city_data[city_key]['lng'] = (city_data[city_key]['lng'] * (city_data[city_key]['count'] - 1) + lng) / city_data[city_key]['count']

                    row_count += 1
                    # Limit processing for faster loading - only process first 50000 rows
                    if row_count > 50000:
                        break

                except (ValueError, TypeError):
                    continue

    # Convert to list and calculate average severity
    cities_list = []
    for city_key, data in city_data.items():
        if data['total_accidents'] > 0:
            avg_severity = data['severity_sum'] / data['total_accidents'] if data['total_accidents'] > 0 else 2
            cities_list.append({
                'city': data['city'],
                'state': data['state'],
                'lat': data['lat'],
                'lng': data['lng'],
                'accidents': data['total_accidents'],
                'avg_severity': round(avg_severity, 1)
            })

    # Sort by accidents and return top 100 cities only (faster)
    cities_list.sort(key=lambda x: x['accidents'], reverse=True)
    return cities_list[:100]  # Top 100 cities for better performance

def get_accident_hotspots():
    """Get accident hotspot data for route overlay"""
    csv_path = os.path.join(settings.BASE_DIR, "..", "data", "accidents_city_detail.csv")
    hotspots = []

    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    lat = float(row.get("Start_Lat", 0))
                    lng = float(row.get("Start_Lng", 0))
                    accidents = int(row.get("Total Accidents", 0))
                    severity = int(row.get("Severity", 2))

                    if accidents > 0 and count < 500:  # Limit to 500 for performance
                        hotspots.append({
                            'lat': lat,
                            'lng': lng,
                            'accidents': accidents,
                            'severity': severity
                        })
                        count += 1
                except (ValueError, TypeError):
                    continue

    return hotspots

def route_page(request):
    # Get current time and weather
    current_hour = datetime.now().hour
    current_weather = get_current_weather_for_routes()

    # Get city data (limited to top 100 for performance)
    city_routes_data = get_city_routes_data()

    # Select top 10 cities for route generation (smaller for faster loading)
    top_cities = city_routes_data[:10] if city_routes_data else []

    context = {
        'current_hour': current_hour,
        'current_weather': current_weather,
        'city_routes_data': json.dumps(city_routes_data),  # Top 100 cities
        'top_cities': json.dumps(top_cities),  # Top 10 for routes
        'openweather_api_key': settings.OPENWEATHER_API_KEY  # For dynamic weather updates
    }

    return render(request, "route_map.html", context)

def select_destination(request):
    return render(request, "select_destination.html")

def start_trip(request):
    # Get destination coordinates from GET or POST
    end_lat = request.GET.get("end_lat")
    end_lon = request.GET.get("end_lon")

    if not end_lat or not end_lon:
        return render(request, "error.html", {"message": "Please pick a destination."})

    weather_risk = get_weather_risk(end_lat, end_lon)

    return render(request, "start_trip.html", {"weather_risk": weather_risk})
