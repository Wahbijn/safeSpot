from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    
    # Admin routes
    path("admin/clients/", views.admin_clients_list, name="admin_clients_list"),
    # path("admin/clients/add/", views.admin_client_add, name="admin_client_add"),  # Disabled: Users can only register themselves
    path("admin/clients/<int:client_id>/edit/", views.admin_client_edit, name="admin_client_edit"),
    path("admin/clients/<int:client_id>/delete/", views.admin_client_delete, name="admin_client_delete"),
]
