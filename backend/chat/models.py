from django.db import models
from accounts.models import CustomUser


class Conversation(models.Model):
    """Chat conversation between employee and AI assistant."""
    title = models.CharField(max_length=200, default="New Conversation")
    employee = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="conversations"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
    
    def __str__(self):
        return f"{self.title} - {self.employee.get_full_name()}"
    
    @property
    def last_message_time(self):
        return self.messages.last().created_at if self.messages.exists() else self.updated_at


class Message(models.Model):
    """Individual chat message."""
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]
    
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sources = models.JSONField(
        default=dict,
        blank=True,
        help_text="Document sources cited in assistant response",
    )
    
    class Meta:
        ordering = ["created_at"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."