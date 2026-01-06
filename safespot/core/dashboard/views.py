from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import Profile, User
from incidents.models import Accident, UserAccidentReport
from incidents.forms import UserAccidentReportForm
from django.conf import settings
import os
import csv
import requests
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate, ExtractHour
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


def calculate_weather_risk(weather_id, temp, humidity, wind_speed):
    """Calculate accident risk percentage based on weather conditions"""
    risk_score = 0

    # Base risk from weather condition ID
    # 2xx: Thunderstorm (very high risk)
    if 200 <= weather_id < 300:
        risk_score += 45
    # 3xx: Drizzle (medium risk)
    elif 300 <= weather_id < 400:
        risk_score += 25
    # 5xx: Rain (high risk)
    elif 500 <= weather_id < 600:
        risk_score += 35
    # 6xx: Snow (very high risk)
    elif 600 <= weather_id < 700:
        risk_score += 50
    # 7xx: Atmosphere (fog, mist, etc. - high risk)
    elif 700 <= weather_id < 800:
        risk_score += 40
    # 800: Clear (low risk)
    elif weather_id == 800:
        risk_score += 5
    # 80x: Clouds (low-medium risk)
    elif 801 <= weather_id < 900:
        risk_score += 15

    # Temperature risk (extreme temps increase risk)
    if temp < 0:  # Freezing
        risk_score += 15
    elif temp < 5:  # Very cold
        risk_score += 10
    elif temp > 35:  # Very hot
        risk_score += 8

    # Humidity risk (high humidity = reduced visibility)
    if humidity > 85:
        risk_score += 10
    elif humidity > 70:
        risk_score += 5

    # Wind speed risk (m/s)
    if wind_speed > 15:  # Strong wind
        risk_score += 12
    elif wind_speed > 10:  # Moderate wind
        risk_score += 7
    elif wind_speed > 7:  # Light wind
        risk_score += 3

    # Cap at 100%
    return min(risk_score, 100)


def get_current_weather(city="Tunis"):
    """Fetch current weather from OpenWeatherMap API"""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return None

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        temp = round(data['main']['temp'], 1)
        humidity = data['main']['humidity']
        wind_speed = round(data['wind']['speed'], 1)
        weather_id = data['weather'][0]['id']

        # Calculate risk based on weather conditions
        risk_score = calculate_weather_risk(weather_id, temp, humidity, wind_speed)

        return {
            'temp': temp,
            'feels_like': round(data['main']['feels_like'], 1),
            'temp_min': round(data['main']['temp_min'], 1),
            'temp_max': round(data['main']['temp_max'], 1),
            'humidity': humidity,
            'weather': data['weather'][0]['main'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'wind_speed': wind_speed,
            'weather_id': weather_id,
            'risk_score': risk_score,
            'city': data['name']
        }
    except Exception as e:
        print(f"Error fetching current weather: {e}")
        return None


def get_weather_forecast(city="Tunis"):
    """Fetch 5-day weather forecast from OpenWeatherMap API"""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return None

    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Process the data to get daily forecasts (every 24 hours)
        forecast_list = data.get('list', [])
        daily_forecasts = []

        # Get one forecast per day at noon (12:00:00)
        for item in forecast_list:
            dt_txt = item.get('dt_txt', '')
            if '12:00:00' in dt_txt:
                date_obj = datetime.strptime(dt_txt, '%Y-%m-%d %H:%M:%S')
                daily_forecasts.append({
                    'date': date_obj.strftime('%a, %b %d'),
                    'temp': round(item['main']['temp'], 1),
                    'temp_min': round(item['main']['temp_min'], 1),
                    'temp_max': round(item['main']['temp_max'], 1),
                    'weather': item['weather'][0]['main'],
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon'],
                    'humidity': item['main']['humidity'],
                    'wind_speed': round(item['wind']['speed'], 1)
                })

                if len(daily_forecasts) >= 5:
                    break

        return daily_forecasts
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None


def get_top_cities_risk_analysis():
    """Get top cities by accident count with their hourly distribution and cost"""
    accidents_by_city_path = os.path.join(
        settings.BASE_DIR, "..", "data", "accidents_by_city.csv"
    )

    hourly_path = os.path.join(
        settings.BASE_DIR, "..", "data", "accidentbycityandhour.csv"
    )

    # First, get total accidents and costs per city
    city_stats = {}

    if os.path.exists(accidents_by_city_path):
        with open(accidents_by_city_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = (row.get("City") or row.get("\ufeffCity") or "").strip()
                state = (row.get("State") or row.get("\ufeffState") or "").strip()

                if not city:
                    continue

                try:
                    accidents = int(row.get("Total Accidents", 0))
                    cost = float(row.get("Sum of Estimated Accident Cost (Row)", 0))

                    city_key = f"{city}, {state}"

                    if city_key not in city_stats:
                        city_stats[city_key] = {
                            'city': city,
                            'state': state,
                            'total_accidents': 0,
                            'total_cost': 0,
                            'hourly': {h: 0 for h in range(24)}
                        }

                    city_stats[city_key]['total_accidents'] += accidents
                    city_stats[city_key]['total_cost'] += cost

                except (ValueError, TypeError):
                    continue

    # Then, get hourly distribution for each city
    if os.path.exists(hourly_path):
        with open(hourly_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = (row.get("City") or row.get("\ufeffCity") or "").strip()

                if not city:
                    continue

                try:
                    hour = int(row.get("start_hour", 0))
                    accidents = int(row.get("Total Accidents", 0))

                    # Find matching city_key (we need to match with state)
                    for city_key in city_stats:
                        if city_stats[city_key]['city'] == city:
                            if 0 <= hour < 24:
                                city_stats[city_key]['hourly'][hour] += accidents
                            break

                except (ValueError, TypeError):
                    continue

    # Get top 10 cities by accident count
    sorted_cities = sorted(
        city_stats.items(),
        key=lambda x: x[1]['total_accidents'],
        reverse=True
    )[:10]

    # Prepare data for the chart
    city_names = []
    accident_counts = []
    peak_hours = []
    costs_millions = []
    hourly_distributions = []
    city_info_list = []  # For template display

    for city_key, data in sorted_cities:
        city_name = f"{data['city']}, {data['state']}"
        city_names.append(city_name)
        accident_counts.append(data['total_accidents'])
        costs_millions.append(round(data['total_cost'] / 1000000, 2))  # Convert to millions

        # Find peak hour for this city
        peak_hour = max(data['hourly'].items(), key=lambda x: x[1])
        peak_hour_str = f"{peak_hour[0]:02d}:00 ({peak_hour[1]} accidents)"
        peak_hours.append(peak_hour_str)

        # Get hourly distribution for this city
        hourly_dist = [data['hourly'][h] for h in range(24)]
        hourly_distributions.append(hourly_dist)

        # Create combined info for template
        city_info_list.append({
            'name': city_name,
            'peak': peak_hour_str
        })

    return {
        'city_names': city_names,
        'accident_counts': accident_counts,
        'peak_hours': peak_hours,
        'costs_millions': costs_millions,
        'hourly_distributions': hourly_distributions,
        'hours': [f"{h:02d}:00" for h in range(24)],
        'city_info_list': city_info_list  # Combined data for easy template iteration
    }


def get_cities_with_risk_distribution():
    """Get top cities by accident count from accidents_city_detail.csv with their risk distribution"""
    accidents_path = os.path.join(
        settings.BASE_DIR, "..", "data", "accidents_city_detail.csv"
    )

    # Dictionary to store city data: {city_name: {state, total_accidents, severities}}
    city_data = {}

    if os.path.exists(accidents_path):
        with open(accidents_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = (row.get("State") or row.get("\ufeffState") or "").strip()
                city = (row.get("City") or row.get("\ufeffCity") or "").strip()

                if not city or not state:
                    continue

                try:
                    accidents = int(row.get("Total Accidents", 0))
                    severity = int(row.get("Severity", 2))

                    # Create unique key with city and state
                    city_key = f"{city}, {state}"

                    if city_key not in city_data:
                        city_data[city_key] = {
                            'city': city,
                            'state': state,
                            'total_accidents': 0,
                            'severities': {1: 0, 2: 0, 3: 0, 4: 0}
                        }

                    city_data[city_key]['total_accidents'] += accidents
                    if 1 <= severity <= 4:
                        city_data[city_key]['severities'][severity] += accidents

                except (ValueError, TypeError):
                    continue

    # Sort cities by total accidents and get top 20
    sorted_cities = sorted(
        city_data.items(),
        key=lambda x: x[1]['total_accidents'],
        reverse=True
    )[:20]

    # Return list of city names
    return [city_name for city_name, _ in sorted_cities]


def get_accident_map_data():
    """Get detailed accident locations with coordinates for clustered map visualization"""
    accidents_path = os.path.join(
        settings.BASE_DIR, "..", "data", "accidents_city_detail.csv"
    )

    map_data = []

    if os.path.exists(accidents_path):
        with open(accidents_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = (row.get("State") or row.get("\ufeffState") or "").strip()
                city = (row.get("City") or row.get("\ufeffCity") or "").strip()

                if not city or not state:
                    continue

                try:
                    lat = float(row.get("Start_Lat", 0))
                    lng = float(row.get("Start_Lng", 0))
                    accidents = int(row.get("Total Accidents", 0))
                    severity = int(row.get("Severity", 2))
                    month = int(row.get("start_month", 0))

                    # Skip invalid coordinates
                    if lat == 0 or lng == 0 or accidents == 0:
                        continue

                    # Add each location as a separate point for clustering
                    map_data.append({
                        'city': city,
                        'state': state,
                        'lat': lat,
                        'lng': lng,
                        'accidents': accidents,
                        'severity': severity,
                        'month': month
                    })

                except (ValueError, TypeError):
                    continue

    # Return all data points for clustering
    return map_data


@login_required(login_url='login')
def dashboard_home(request):
    from predictions.models import PredictionHistory
    from django.utils import timezone

    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    # Count only client users (exclude admins)
    total_users = User.objects.filter(role='client').count()
    total_accidents = UserAccidentReport.objects.count()

    # Calculate total predictions count (all users)
    total_predictions_count = PredictionHistory.objects.count()

    # Calculate daily predictions (today only)
    today = timezone.now().date()
    daily_predictions_count = PredictionHistory.objects.filter(
        created_at__date=today
    ).count()

    # Calculate user's predictions
    user_predictions_count = PredictionHistory.objects.filter(user=user).count()
    user_daily_predictions = PredictionHistory.objects.filter(
        user=user,
        created_at__date=today
    ).count()

    # Count user's reported accidents (UserAccidentReport uses 'created_by' field)
    reported_accidents_count = UserAccidentReport.objects.filter(created_by=user).count()

    top_user_incidents = UserAccidentReport.objects.order_by('-accident_datetime')[:3]
    top_accidents = Accident.objects.order_by('-accident_datetime')[:3]

    # -------------------------------
    # OVERALL ACCIDENT DISTRIBUTION BY SEVERITY
    # -------------------------------
    severity_csv_path = os.path.join(
        settings.BASE_DIR, "..", "data", "Total Accidents by Severity.csv"
    )

    severity_distribution = {
        "Low": 0,
        "Medium": 0,
        "High": 0,
        "Critical": 0
    }

    severity_map = {
        "1": "Low",
        "2": "Medium",
        "3": "High",
        "4": "Critical",
    }

    if os.path.exists(severity_csv_path):
        with open(severity_csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                severity_code = (row.get("Severity") or row.get("\ufeffSeverity") or "").strip()
                total = int(row.get("Total Accidents", 0))

                severity_label = severity_map.get(severity_code)
                if severity_label:
                    severity_distribution[severity_label] = total

    # Calculate percentages
    total_all_accidents = sum(severity_distribution.values())
    risk_labels = ["Low", "Medium", "High", "Critical"]
    risk_values = []
    risk_counts = []

    for severity in risk_labels:
        count = severity_distribution[severity]
        percent = round((count / total_all_accidents) * 100, 2) if total_all_accidents else 0
        risk_values.append(percent)
        risk_counts.append(count)

    # -------------------------------
    # WEATHER DATA
    # -------------------------------
    weather_city = "Tunis"  # Default city for weather
    current_weather = get_current_weather(weather_city)
    weather_forecast = get_weather_forecast(weather_city)

    # -------------------------------
    # TOP CITIES RISK ANALYSIS
    # -------------------------------
    top_cities_analysis = get_top_cities_risk_analysis()

    # -------------------------------
    # MAP DATA
    # -------------------------------
    map_data = get_accident_map_data()

    # -------------------------------
    # CITIES FOR RISK DISTRIBUTION FILTER
    # -------------------------------
    cities_for_filter = get_cities_with_risk_distribution()

    # -------------------------------
    # VEHICLE DATABASE FOR COST PREDICTOR
    # -------------------------------
    vehicle_db_path = os.path.join(settings.BASE_DIR, "..", "data", "vehicle_database.csv")
    vehicle_makes = set()
    vehicle_data = {}

    if os.path.exists(vehicle_db_path):
        with open(vehicle_db_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                make = row['make']
                model = row['model']
                vehicle_makes.add(make)

                if make not in vehicle_data:
                    vehicle_data[make] = []

                vehicle_data[make].append({
                    'model': model,
                    'min_year': int(row['min_year']),
                    'max_year': int(row['max_year']),
                    'base_value': int(row['base_value']),
                    'category': row['category']
                })

    context = {
        "user": user,
        "profile": profile,
        "total_users": total_users,
        "total_accidents": total_accidents,
        "top_user_incidents": top_user_incidents,
        "top_accidents": top_accidents,

        # 🔽 PREDICTIONS DATA
        "total_predictions_count": total_predictions_count,  # All predictions
        "daily_predictions_count": daily_predictions_count,  # Today's predictions (all users)
        "user_predictions_count": user_predictions_count,  # User's total predictions
        "user_daily_predictions": user_daily_predictions,  # User's daily predictions
        "reported_accidents_count": reported_accidents_count,  # User's reported accidents

        # 🔽 OVERALL RISK DISTRIBUTION DATA
        "risk_labels": risk_labels,
        "risk_values": risk_values,
        "risk_counts": risk_counts,
        "total_all_accidents": total_all_accidents,

        # 🔽 WEATHER DATA
        "current_weather": current_weather,
        "weather_forecast": weather_forecast,
        "weather_city": weather_city,
        "openweather_api_key": settings.OPENWEATHER_API_KEY,

        # 🔽 TOP CITIES RISK ANALYSIS DATA
        "top_city_names": top_cities_analysis['city_names'],
        "top_accident_counts": top_cities_analysis['accident_counts'],
        "top_peak_hours": top_cities_analysis['peak_hours'],
        "top_costs_millions": top_cities_analysis['costs_millions'],
        "top_hourly_distributions": top_cities_analysis['hourly_distributions'],
        "analysis_hours": top_cities_analysis['hours'],
        "city_info_list": top_cities_analysis['city_info_list'],

        # 🔽 CITIES FOR RISK DISTRIBUTION FILTER (from accidents_city_detail.csv)
        "cities_for_filter": cities_for_filter,

        # 🔽 VEHICLE DATABASE FOR COST PREDICTOR
        "vehicle_makes": sorted(vehicle_makes),
        "vehicle_data": vehicle_data,

        # 🔽 MAP DATA
        "map_data": map_data,
    }

    return render(request, "dashboard/dashboard.html", context)


@require_http_methods(["GET"])
@login_required(login_url='login')
def get_weather_api(request, city):
    """API endpoint to fetch weather data for a city via AJAX"""
    current_weather = get_current_weather(city)
    forecast = get_weather_forecast(city)

    return JsonResponse({
        'success': True,
        'current_weather': current_weather,
        'forecast': forecast,
        'city': city
    })


@require_http_methods(["POST"])
@login_required(login_url='login')
def predict_accident_cost(request):
    """API endpoint to predict accident cost based on vehicle and accident details"""
    import json

    try:
        data = json.loads(request.body)

        # Extract parameters (simplified - focus on core features)
        vehicle_make = data.get('vehicle_make', '')
        vehicle_model = data.get('vehicle_model', '')
        vehicle_year = int(data.get('vehicle_year', 2020))
        severity = int(data.get('severity', 2))
        damage_type = data.get('damage_type', 'Moderate')
        road_type = data.get('road_type', 'Urban')

        # Use default values for removed features
        num_vehicles = 1
        time_hour = 12  # Daytime default
        injuries = 0    # No injuries default

        # Load vehicle database to get base value
        vehicle_db_path = os.path.join(settings.BASE_DIR, "..", "data", "vehicle_database.csv")
        vehicle_value = 25000  # Default value

        if os.path.exists(vehicle_db_path):
            with open(vehicle_db_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row['make'].lower() == vehicle_make.lower() and
                        row['model'].lower() == vehicle_model.lower()):
                        vehicle_value = int(row['base_value'])
                        break

        # Apply depreciation based on age
        current_year = 2024
        age = current_year - vehicle_year
        depreciation = 0.85 ** age
        current_value = int(vehicle_value * depreciation)

        # Damage type multipliers (more realistic)
        damage_multipliers = {
            'Minor': {'repair_pct': 0.15, 'base': 1000},      # 15% of value + $1,000
            'Moderate': {'repair_pct': 0.35, 'base': 3000},   # 35% of value + $3,000
            'Severe': {'repair_pct': 0.65, 'base': 5000},     # 65% of value + $5,000
            'Total Loss': {'repair_pct': 1.0, 'base': 0}      # 100% of vehicle value
        }

        damage_info = damage_multipliers.get(damage_type, damage_multipliers['Moderate'])

        # Calculate repair cost
        if damage_type == 'Total Loss':
            # Total loss = full vehicle value (can't repair, need to replace)
            repair_cost = current_value
        else:
            # Other damage types: base cost + percentage of vehicle value
            repair_cost = damage_info['base'] + (current_value * damage_info['repair_pct'])
            # Cap repair cost at 95% of vehicle value (beyond that, it's total loss)
            repair_cost = min(repair_cost, current_value * 0.95)

        # Luxury/electric vehicle multiplier
        luxury_makes = ['BMW', 'Mercedes-Benz', 'Tesla', 'Audi', 'Lexus']
        if vehicle_make in luxury_makes:
            repair_cost *= 1.5

        # Medical costs based on severity and injuries
        medical_base = {1: 2000, 2: 8000, 3: 25000, 4: 80000}
        medical_cost = medical_base.get(severity, 8000)
        if injuries > 0:
            medical_cost *= (1 + injuries * 0.5)

        # Road type multiplier
        road_multipliers = {
            'Highway': 1.3,
            'Urban': 1.1,
            'Residential': 0.9,
            'Rural': 1.0
        }
        road_mult = road_multipliers.get(road_type, 1.0)

        # Time multiplier (night accidents more expensive)
        time_mult = 1.2 if (22 <= time_hour or time_hour <= 5) else 1.0

        # Additional costs
        towing = 250 if damage_type != 'Minor' else 0
        legal_fees = 3000 if severity >= 3 else 0
        administrative = 500

        # Calculate total with multipliers
        base_total = repair_cost + medical_cost + towing + legal_fees + administrative
        total_cost = base_total * road_mult * time_mult

        # Multiple vehicles increase cost
        total_cost *= (1 + (num_vehicles - 1) * 0.3)

        total_cost = int(total_cost)
        repair_cost = int(repair_cost)
        medical_cost = int(medical_cost)

        # Calculate cost range (±15%)
        cost_min = int(total_cost * 0.85)
        cost_max = int(total_cost * 1.15)

        # Calculate confidence based on data quality
        confidence = 85
        if vehicle_make and vehicle_model:
            confidence += 5
        if damage_type in damage_multipliers:
            confidence += 5
        confidence = min(confidence, 95)

        # Determine risk level
        if total_cost < 10000:
            risk_level = 'Low'
            gauge_percent = 25
        elif total_cost < 50000:
            risk_level = 'Medium'
            gauge_percent = 50
        elif total_cost < 100000:
            risk_level = 'High'
            gauge_percent = 75
        else:
            risk_level = 'Critical'
            gauge_percent = 100

        # Save prediction to history
        from predictions.models import PredictionHistory
        PredictionHistory.objects.create(
            user=request.user,
            vehicle_make=vehicle_make,
            vehicle_model=vehicle_model,
            vehicle_year=vehicle_year,
            damage_type=damage_type,
            severity=severity,
            road_type=road_type,
            total_cost=total_cost,
            repair_cost=repair_cost,
            medical_cost=medical_cost,
            other_costs=towing + legal_fees + administrative,
            vehicle_value=current_value
        )

        return JsonResponse({
            'success': True,
            'total_cost': total_cost,
            'cost_min': cost_min,
            'cost_max': cost_max,
            'repair_cost': repair_cost,
            'medical_cost': medical_cost,
            'other_costs': towing + legal_fees + administrative,
            'vehicle_value': current_value,
            'confidence': confidence,
            'risk_level': risk_level,
            'gauge_percent': gauge_percent
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
@login_required(login_url='login')
def get_city_risk_distribution(request, city):
    """API endpoint to fetch risk distribution data for a specific city"""
    accidents_path = os.path.join(
        settings.BASE_DIR, "..", "data", "accidents_city_detail.csv"
    )

    severity_distribution = {
        "Low": 0,
        "Medium": 0,
        "High": 0,
        "Critical": 0
    }

    severity_map = {
        1: "Low",
        2: "Medium",
        3: "High",
        4: "Critical",
    }

    total_accidents = 0

    # Extract city name from "City, State" format
    # e.g., "Anaheim, CA" -> city_name = "Anaheim", state_code = "CA"
    city_parts = city.split(',')
    city_name = city_parts[0].strip() if city_parts else city
    state_code = city_parts[1].strip() if len(city_parts) > 1 else None

    if os.path.exists(accidents_path):
        with open(accidents_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_city = (row.get("City") or row.get("\ufeffCity") or "").strip()
                row_state = (row.get("State") or row.get("\ufeffState") or "").strip()

                # Match by city name (and optionally state if provided)
                city_match = row_city.lower() == city_name.lower()
                state_match = (state_code is None) or (row_state.lower() == state_code.lower())

                if city_match and state_match:
                    try:
                        severity = int(row.get("Severity", 0))
                        accidents = int(row.get("Total Accidents", 0))

                        severity_label = severity_map.get(severity)
                        if severity_label:
                            severity_distribution[severity_label] += accidents
                            total_accidents += accidents
                    except (ValueError, TypeError):
                        continue

    # Calculate percentages
    risk_labels = ["Low", "Medium", "High", "Critical"]
    risk_values = []
    risk_counts = []

    for severity in risk_labels:
        count = severity_distribution[severity]
        percent = round((count / total_accidents) * 100, 2) if total_accidents else 0
        risk_values.append(percent)
        risk_counts.append(count)

    return JsonResponse({
        'success': True,
        'risk_values': risk_values,
        'risk_counts': risk_counts,
        'risk_labels': risk_labels,
        'total_accidents': total_accidents,
        'city': city
    })


@login_required(login_url='login')
def export_predictions_report(request):
    """Export user's prediction history as a beautiful PDF report"""
    from predictions.models import PredictionHistory
    from django.template.loader import render_to_string
    from django.http import HttpResponse

    # Get user's predictions
    predictions = PredictionHistory.objects.filter(user=request.user).order_by('-created_at')

    # Calculate summary statistics
    total_predictions = predictions.count()
    if total_predictions == 0:
        return HttpResponse("No predictions found. Please make some predictions first.", status=404)

    # Get selected prediction ID from URL parameter (default to latest)
    selected_id = request.GET.get('prediction_id')

    if selected_id:
        try:
            latest_prediction = predictions.get(id=selected_id)
        except PredictionHistory.DoesNotExist:
            latest_prediction = predictions.first()
    else:
        latest_prediction = predictions.first()

    # Use latest prediction values for main stats
    total_cost_sum = float(latest_prediction.total_cost)
    total_repair = float(latest_prediction.repair_cost)
    total_medical = float(latest_prediction.medical_cost)
    total_other = float(latest_prediction.other_costs)

    # Calculate percentages for chart (from latest prediction)
    repair_percent = (total_repair / total_cost_sum * 100) if total_cost_sum > 0 else 0
    medical_percent = (total_medical / total_cost_sum * 100) if total_cost_sum > 0 else 0
    other_percent = (total_other / total_cost_sum * 100) if total_cost_sum > 0 else 0

    # Calculate historical averages (from all predictions)
    historical_avg = sum(float(p.total_cost) for p in predictions) / total_predictions if total_predictions > 0 else 0
    max_cost_prediction = predictions.order_by('-total_cost').first()
    min_cost_prediction = predictions.order_by('total_cost').first()

    context = {
        'user': request.user,
        'latest_prediction': latest_prediction,
        'selected_prediction_id': latest_prediction.id,
        'all_predictions': predictions,  # All predictions for dropdown
        'predictions': predictions[:20],  # Show latest 20 in table
        'total_predictions': total_predictions,
        'total_cost_sum': total_cost_sum,  # Now from selected prediction
        'avg_cost': historical_avg,  # Historical average
        'max_cost_prediction': max_cost_prediction,
        'min_cost_prediction': min_cost_prediction,
        'total_repair': total_repair,  # From selected prediction
        'total_medical': total_medical,  # From selected prediction
        'total_other': total_other,  # From selected prediction
        'repair_percent': repair_percent,
        'medical_percent': medical_percent,
        'other_percent': other_percent,
        'report_date': datetime.now(),
    }

    return render(request, 'dashboard/export_report.html', context)


@login_required(login_url='login')
def check_predictions_exist(request):
    """API endpoint to check if user has any predictions"""
    from predictions.models import PredictionHistory

    count = PredictionHistory.objects.filter(user=request.user).count()

    return JsonResponse({
        'has_predictions': count > 0,
        'count': count
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_prediction(request, prediction_id):
    """Delete a specific prediction"""
    from predictions.models import PredictionHistory

    try:
        prediction = PredictionHistory.objects.get(id=prediction_id, user=request.user)
        prediction.delete()
        return JsonResponse({
            'success': True,
            'message': 'Prediction deleted successfully'
        })
    except PredictionHistory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Prediction not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_all_predictions(request):
    """Delete all predictions for the current user"""
    from predictions.models import PredictionHistory

    try:
        # Get count before deletion
        count = PredictionHistory.objects.filter(user=request.user).count()

        # Delete all predictions for this user
        PredictionHistory.objects.filter(user=request.user).delete()

        return JsonResponse({
            'success': True,
            'message': f'{count} predictions deleted successfully',
            'deleted_count': count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

