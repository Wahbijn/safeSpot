from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from .models import Conversation, Message
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json

@login_required
def client_send_message(request):
    # client envoie message à admin
    user = request.user
    conversation, created = Conversation.objects.get_or_create(client=user)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Get admin user (first admin found)
            User = get_user_model()
            admin_user = User.objects.filter(role='admin').first()
            if admin_user:
                Message.objects.create(
                    conversation=conversation,
                    sender_user=user,
                    receiver_user=admin_user,
                    body=content,
                    sent_at=timezone.now(),
                    read=False
                )
            return redirect('messaging:client_conversation')
    return redirect('messaging:client_conversation')

@login_required
def client_conversation_view(request):
    user = request.user
    conversation, _ = Conversation.objects.get_or_create(client=user)
    messages = conversation.messages.all()
    return render(request, 'messaging/client_conversation.html', {'conversation': conversation, 'messages': messages})

@login_required
def admin_inbox(request):
    # restreindre aux admins (ex: user.role == 'admin' ou is_staff)
    if not request.user.is_staff:
        return redirect('dashboard_home')
    conversations = Conversation.objects.select_related('client').all().order_by('-messages__created_at')
    return render(request, 'messaging/admin_inbox.html', {'conversations': conversations})

@login_required
def admin_conversation_view(request, client_id):
    if not request.user.is_staff:
        return redirect('dashboard_home')
    conv = get_object_or_404(Conversation, client__id=client_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            User = get_user_model()
            Message.objects.create(
                conversation=conv,
                sender_user=request.user,
                receiver_user=conv.client,
                body=content,
                sent_at=timezone.now(),
                read=False
            )
            # marquer message reçu du client comme lu si nécessaire
            return redirect('messaging:admin_conversation', client_id=client_id)
    # Mark client messages as read by admin when admin opens
    conv.messages.filter(read=False).exclude(sender_user__role='admin').update(read=True)
    messages = conv.messages.all()
    return render(request, 'messaging/admin_conversation.html', {'conversation': conv, 'messages': messages})

@login_required
def unread_count_api(request):
    # retourne le nombre total de messages non lus pour admin
    if not request.user.is_staff:
        return JsonResponse({'unread': 0})
    count = Message.objects.filter(conversation__isnull=False, read=False).exclude(sender_user__role='admin').count()
    return JsonResponse({'unread': count})


@login_required
def users_list(request):
    """Return a list of users to start a conversation with.

    For clients we show admin users; for admins we show clients.
    """
    User = get_user_model()
    role = getattr(request.user, 'role', None)
    if role == 'admin':
        users = User.objects.filter(role='client').exclude(pk=request.user.pk).order_by('username')
    else:
        users = User.objects.filter(role='admin').exclude(pk=request.user.pk).order_by('username')

    return render(request, 'messaging/users_list.html', {'users': users})


# New API Endpoints for Real-time Chat
@login_required
@require_http_methods(["GET"])
def get_messages_api(request):
    """Get all messages for current user's conversation"""
    user = request.user
    User = get_user_model()

    # Get or create conversation
    if getattr(user, 'role', None) == 'admin':
        # For admin, show most recent conversation
        # Later we can add UI to select which user to chat with
        latest_conversation = Conversation.objects.order_by('-created_at').first()

        if not latest_conversation:
            return JsonResponse({'messages': []})

        messages = latest_conversation.messages.all().order_by('sent_at')

        # Mark user messages as read by admin
        latest_conversation.messages.filter(
            read=False,
            sender_user=latest_conversation.client
        ).update(read=True)

        messages_data = []
        for msg in messages:
            is_from_admin = msg.sender_user and getattr(msg.sender_user, 'role', None) == 'admin'
            messages_data.append({
                'from': 'admin' if is_from_admin else 'user',
                'text': msg.body,
                'time': msg.sent_at.strftime('%I:%M %p') if msg.sent_at else '',
                'read': msg.read,
                'id': msg.id
            })

        return JsonResponse({'messages': messages_data})
    else:
        # For regular user - show their own conversation
        conversation, created = Conversation.objects.get_or_create(client=user)
        messages = conversation.messages.all().order_by('sent_at')

        # Mark admin messages as read
        conversation.messages.filter(
            read=False
        ).exclude(sender_user=user).update(read=True)

        messages_data = []
        for msg in messages:
            is_from_admin = msg.sender_user and getattr(msg.sender_user, 'role', None) == 'admin'
            messages_data.append({
                'from': 'admin' if is_from_admin else 'user',
                'text': msg.body,
                'time': msg.sent_at.strftime('%I:%M %p') if msg.sent_at else '',
                'read': msg.read,
                'id': msg.id
            })

        return JsonResponse({'messages': messages_data})


@login_required
@require_http_methods(["POST"])
def send_message_api(request):
    """Send a new message"""
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        client_id = data.get('client_id')  # For admin to specify which client to message

        if not message_text:
            return JsonResponse({'success': False, 'error': 'Empty message'})

        user = request.user
        User = get_user_model()

        # Determine conversation and receiver based on user role
        if getattr(user, 'role', None) == 'admin':
            # Admin sending - use client_id if provided
            if client_id:
                try:
                    conversation = Conversation.objects.get(client__id=client_id)
                except Conversation.DoesNotExist:
                    client_user = User.objects.get(id=client_id)
                    conversation, _ = Conversation.objects.get_or_create(client=client_user)
            else:
                # No client_id provided - use most recent conversation
                latest_conversation = Conversation.objects.order_by('-created_at').first()

                if not latest_conversation:
                    # No conversations yet - need a client to message
                    client_user = User.objects.filter(role='client').first()
                    if not client_user:
                        return JsonResponse({'success': False, 'error': 'No clients to message'})
                    conversation, _ = Conversation.objects.get_or_create(client=client_user)
                else:
                    conversation = latest_conversation

            receiver = conversation.client
        else:
            # Regular user sending to admin
            conversation, _ = Conversation.objects.get_or_create(client=user)
            receiver = User.objects.filter(role='admin').first()

        if not receiver:
            return JsonResponse({'success': False, 'error': 'No receiver found'})

        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender_user=user,
            receiver_user=receiver,
            body=message_text,
            sent_at=timezone.now(),
            read=False
        )

        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'from': 'admin' if getattr(user, 'role', None) == 'admin' else 'user',
                'text': message.body,
                'time': message.sent_at.strftime('%I:%M %p'),
                'read': message.read
            }
        })

    except Exception as e:
        import traceback
        print(f"Error in send_message_api: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def get_unread_count_api(request):
    """Get unread message count for current user"""
    user = request.user

    if getattr(user, 'role', None) == 'admin':
        # Count unread messages from all clients
        count = Message.objects.filter(
            read=False
        ).exclude(sender_user__role='admin').count()
    else:
        # Count unread messages from admin for this specific user
        try:
            conversation = Conversation.objects.get(client=user)
            count = conversation.messages.filter(
                read=False
            ).exclude(sender_user=user).count()
        except Conversation.DoesNotExist:
            count = 0

    return JsonResponse({'unread': count})


@login_required
@require_http_methods(["GET"])
def get_conversations_api(request):
    """Get list of all conversations for admin"""
    user = request.user

    if getattr(user, 'role', None) != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    conversations = Conversation.objects.select_related('client').all().order_by('-created_at')

    conversations_data = []
    for conv in conversations:
        # Get last message
        last_message = conv.messages.order_by('-sent_at').first()

        # Get unread count for this conversation
        unread_count = conv.messages.filter(read=False).exclude(sender_user__role='admin').count()

        conversations_data.append({
            'id': conv.id,
            'client_id': conv.client.id,
            'client_name': conv.client.username if hasattr(conv.client, 'username') else 'User',
            'client_email': conv.client.email if hasattr(conv.client, 'email') else '',
            'last_message': last_message.body if last_message else 'No messages yet',
            'last_message_time': last_message.sent_at.strftime('%I:%M %p') if last_message and last_message.sent_at else '',
            'unread_count': unread_count,
            'created_at': conv.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return JsonResponse({'conversations': conversations_data})


@login_required
@require_http_methods(["GET"])
def get_conversation_messages_api(request, client_id):
    """Get messages for a specific conversation"""
    user = request.user

    if getattr(user, 'role', None) != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        conversation = Conversation.objects.get(client__id=client_id)

        # Mark messages as read
        conversation.messages.filter(read=False).exclude(sender_user__role='admin').update(read=True)

        messages = conversation.messages.all().order_by('sent_at')

        messages_data = []
        for msg in messages:
            is_from_admin = msg.sender_user and getattr(msg.sender_user, 'role', None) == 'admin'
            messages_data.append({
                'from': 'admin' if is_from_admin else 'user',
                'text': msg.body,
                'time': msg.sent_at.strftime('%I:%M %p') if msg.sent_at else '',
                'read': msg.read,
                'id': msg.id
            })

        return JsonResponse({
            'messages': messages_data,
            'client_name': conversation.client.username if hasattr(conversation.client, 'username') else 'User',
            'client_email': conversation.client.email if hasattr(conversation.client, 'email') else ''
        })

    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
