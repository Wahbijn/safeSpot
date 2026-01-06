from django.urls import path
from . import views

app_name = "routes"

urlpatterns = [
    path("", views.select_destination, name="select"),
    path("route-map/", views.route_page, name="route_page"),
    path("start-trip/", views.start_trip, name="start_trip"),
]

