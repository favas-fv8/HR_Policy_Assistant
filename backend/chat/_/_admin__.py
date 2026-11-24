from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "employee", "title", "created_at", "updated_at", "is_active"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["title", "employee__username", "employee__email"]
    date_hierarchy = "created_at"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "role", "created_at", "sources_preview"]
    list_filter = ["role", "created_at"]
    search_fields = ["content"]
    
    def sources_preview(self, obj):
        return str(obj.sources)[:50] if obj.sources else "-"
    sources_preview.short_description = "Sources"