# core/context_processors.py
from messaging.models import Message

def admin_notifications(request):
    if request.user.is_authenticated and request.user.is_staff:
        new_messages_count = Message.objects.filter(receiver_user=request.user, read=False).count()
        new_messages = Message.objects.filter(receiver_user=request.user, read=False)
        return {
            'new_messages_count': new_messages_count,
            'new_messages': new_messages,
        }
    return {}

def admin_unread_count(request):
    if request.user.is_authenticated and request.user.is_staff:
        count = Message.objects.filter(sender_user__role='client', read=False).count()
    else:
        count = 0
    return {'admin_unread_count': count}
