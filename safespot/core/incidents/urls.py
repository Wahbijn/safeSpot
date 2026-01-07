from django.urls import path
from . import views

app_name = 'incidents'

urlpatterns = [
    path('add-accident/', views.add_accident, name='add_accident'),
    path('add-user-accident-report/', views.add_user_accident_report, name='add_user_accident_report'),
    path('', views.accident_list, name='accident_list'),
    path('incidents/', views.incident_list, name='incident_list'),
    path('confirm/<int:accident_id>/', views.confirm_accident, name='confirm_accident'),
    path('cancel/<int:accident_id>/', views.cancel_accident, name='cancel_accident'),

    # Pending incidents (Need confirmation)
    path('pending/', views.pending_incidents, name='pending_incidents'),
    path('api/confirm/<int:incident_id>/', views.confirm_incident_ajax, name='confirm_incident_ajax'),
    path('api/reject/<int:incident_id>/', views.reject_incident_ajax, name='reject_incident_ajax'),
]