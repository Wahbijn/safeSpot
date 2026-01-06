def generate_alerts(weather_risk):
    alerts = []

    if weather_risk["is_dangerous"]:
        alerts.append(
            f"⚠ Dangerous weather detected: {', '.join(weather_risk['danger'])}"
        )

    if weather_risk["temperature"] < 3:
        alerts.append("❄ Risk of icy roads")

    return alerts
