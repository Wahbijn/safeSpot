from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    # Backwards-compatible send endpoint
    path('send/', views.client_send_message, name='send'),
    path('send/', views.client_send_message, name='send_message'),
    path('client/send/', views.client_send_message, name='client_send'),
    path('client/conversation/', views.client_conversation_view, name='client_conversation'),
    path('users/', views.users_list, name='users_list'),
    path('admin/inbox/', views.admin_inbox, name='admin_inbox'),
    path('admin/conversation/<int:client_id>/', views.admin_conversation_view, name='admin_conversation'),
    path('api/unread-count/', views.unread_count_api, name='unread_count_api'),  # pour badge AJAX

    # New Real-time Chat APIs
    path('api/messages/', views.get_messages_api, name='get_messages_api'),
    path('api/send/', views.send_message_api, name='send_message_api'),
    path('api/unread/', views.get_unread_count_api, name='get_unread_api'),
    path('api/conversations/', views.get_conversations_api, name='get_conversations_api'),
    path('api/conversation/<int:client_id>/', views.get_conversation_messages_api, name='get_conversation_messages_api'),
]
