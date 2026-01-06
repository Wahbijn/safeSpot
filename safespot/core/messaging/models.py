from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Conversation(models.Model):
    client = models.OneToOneField(User, on_delete=models.CASCADE, related_name='conversation')
    created_at = models.DateTimeField(auto_now_add=True)

    def unread_count(self):
        # Count messages in this conversation that are unread by admin
        return self.messages.filter(read=False).exclude(sender_user__role='admin').count()

    def __str__(self):
        # Some projects may not have email set; use repr-friendly string
        return f"Conversation client {getattr(self.client, 'email', str(self.client))}"


class Message(models.Model):
    # Backwards-compatible mapping to the existing DB columns
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', null=True, blank=True, db_column='sender_id')
    receiver_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True, db_column='receiver_id')
    body = models.TextField(db_column='body')
    sent_at = models.DateTimeField(db_column='sent_at', null=True, blank=True)
    read = models.BooleanField(default=False, db_column='read')
    read_at = models.DateTimeField(null=True, blank=True)
    subject = models.CharField(max_length=200, null=True, blank=True, db_column='subject')

    class Meta:
        ordering = ('sent_at',)

    def __str__(self):
        return f"Message {self.pk}"

    @property
    def content(self):
        return self.body

    @property
    def sender(self):
        # Return 'client' or 'admin' based on sender_user.role if available
        try:
            role = getattr(self.sender_user, 'role', None)
            if role == 'client':
                return 'client'
            return 'admin'
        except Exception:
            return 'client'
