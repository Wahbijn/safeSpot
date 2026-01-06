from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path('incidents/', include('incidents.urls')), 
    path("messages/", include(("messaging.urls", "messaging"), namespace='messaging')),
    path("routes/", include("routes.urls")),
    path('', lambda request: redirect('login')),
]
