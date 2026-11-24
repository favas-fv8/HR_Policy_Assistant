from rest_framework import serializers
from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model."""
    employee_name = serializers.CharField(
        source="employee.get_full_name", read_only=True
    )
    
    class Meta:
        model = Conversation
        fields = [
            "id", "title", "employee", "employee_name",
            "created_at", "updated_at", "is_active"
        ]
        read_only_fields = ["employee", "created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    employee_name = serializers.CharField(
        source="conversation.employee.get_full_name", read_only=True
    )
    sources = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id", "conversation", "role", "content",
            "created_at", "sources", "employee_name"
        ]
        read_only_fields = ["conversation"]

    def get_sources(self, obj):
        """Normalize sources to a list of source objects.

        The DB field default is a dict for legacy reasons; some rows may
        contain dict/None. The API contract is always a list.
        """
        raw = obj.sources
        if raw is None:
            return []
        if isinstance(raw, list):
            # keep only dict-like source entries with expected keys
            normalized = []
            for item in raw:
                if isinstance(item, dict):
                    normalized.append({
                        "document_id": item.get("document_id"),
                        "document_title": item.get("document_title") or item.get("title") or "Unknown document",
                        "page_number": item.get("page_number"),
                        "excerpt": item.get("excerpt") or item.get("chunk_text") or "",
                    })
            return normalized
        if isinstance(raw, dict):
            # empty dict or single source dict
            if not raw:
                return []
            if "document_title" in raw or "page_number" in raw or "title" in raw:
                return [{
                    "document_id": raw.get("document_id"),
                    "document_title": raw.get("document_title") or raw.get("title") or "Unknown document",
                    "page_number": raw.get("page_number"),
                    "excerpt": raw.get("excerpt") or raw.get("chunk_text") or "",
                }]
            return []
        return []