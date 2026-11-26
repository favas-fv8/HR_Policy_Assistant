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
        """Normalize sources to a list of source objects."""
        raw = obj.sources
        if raw is None:
            return []
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, dict):
            if not raw:
                return []
            if "document_title" in raw or "page_number" in raw or "title" in raw:
                items = [raw]
            else:
                return []
        else:
            return []

        from documents.models import Document

        normalized = []
        for item in items:
            if not isinstance(item, dict):
                continue
            doc_id = item.get("document_id")
            doc_title = item.get("document_title") or item.get("title") or "Unknown document"
            page_number = item.get("page_number")
            excerpt = item.get("excerpt") or item.get("chunk_text") or ""
            if doc_id is not None:
                try:
                    doc_id_int = int(doc_id)
                except (TypeError, ValueError):
                    doc_id_int = None
                if doc_id_int is not None and not Document.objects.filter(pk=doc_id_int).exists():
                    normalized.append({
                        "document_id": None,
                        "document_title": doc_title,
                        "page_number": None,
                        "excerpt": "",
                        "document_deleted": True,
                    })
                    continue
            normalized.append({
                "document_id": doc_id if (isinstance(doc_id, (int, str)) and doc_id != "") else doc_id,
                "document_title": doc_title,
                "page_number": page_number,
                "excerpt": excerpt,
                "document_deleted": False,
            })
        return normalized