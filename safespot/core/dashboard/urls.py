from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_home, name="dashboard_home"),
    path("api/weather/<str:city>/", views.get_weather_api, name="get_weather_api"),
    path("api/risk-distribution/<str:city>/", views.get_city_risk_distribution, name="get_city_risk_distribution"),
    path("api/predict-cost/", views.predict_accident_cost, name="predict_accident_cost"),
    path("api/pending-incidents-count/", views.get_pending_incidents_count_api, name="get_pending_incidents_count_api"),
    path("export-report/", views.export_predictions_report, name="export_predictions_report"),
    path("api/check-predictions/", views.check_predictions_exist, name="check_predictions_exist"),
    path("api/delete-prediction/<int:prediction_id>/", views.delete_prediction, name="delete_prediction"),
    path("api/delete-all-predictions/", views.delete_all_predictions, name="delete_all_predictions"),
]
