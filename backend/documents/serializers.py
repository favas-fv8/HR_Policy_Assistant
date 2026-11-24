from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for DocumentChunk model (read-only for employees)."""
    document_title = serializers.CharField(source="document.title", read_only=True)

    class Meta:
        model = DocumentChunk
        fields = [
            "id", "document", "document_title", "chunk_index",
            "page_number", "page_start", "page_end", "section_heading",
            "char_count", "token_count", "embedding_status",
            "chunk_text", "created_at"
        ]
        read_only_fields = ["chunk_text"]


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name", read_only=True
    )
    file_url = serializers.SerializerMethodField()
    chunk_count = serializers.SerializerMethodField()
    embedded_chunk_count = serializers.SerializerMethodField()
    processing_error = serializers.SerializerMethodField()
    processing_progress = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id", "title", "filename", "file_url", "file_size",
            "page_count", "extracted_characters", "extracted_tokens", "extraction_tokenizer",
            "status", "uploaded_by_name",
            "uploaded_at", "chunk_count", "embedded_chunk_count", "processing_error",
            "processing_progress", "processing_stage", "processing_stage_detail",
            "total_chunks", "processed_chunks",
            "processing_attempt", "processing_started_at", "processing_completed_at",
        ]
        read_only_fields = ["uploaded_by", "uploaded_at", "status"]

    def get_embedded_chunk_count(self, obj):
        return obj.chunks.filter(embedding_status="embedded").count()

    def get_file_url(self, obj):
        return obj.file.url if obj.file else None

    def get_chunk_count(self, obj):
        # Source of truth: actual stored DocumentChunk records.
        return obj.chunks.count()

    def get_processing_progress(self, obj):
        progress = int(getattr(obj, "processing_progress", 0) or 0)
        if obj.status in {"ready", "completed"}:
            return 100
        if obj.status == "error":
            return max(0, min(99, progress))
        if obj.status == "started":
            return max(0, min(10, progress))
        return max(0, min(99, progress))

    def get_processing_error(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and getattr(user, "is_hr_admin", False):
            return obj.processing_error or ""
        return ""


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document upload (HR Admin only)."""

    class Meta:
        model = Document
        fields = ["title", "file"]

    def validate_file(self, value):
        """Validate uploaded file is PDF and within size limits."""
        import os
        from django.conf import settings

        # Check file extension
        ext = os.path.splitext(value.name)[1].lower()
        if ext != ".pdf":
            raise serializers.ValidationError(
                "Only PDF files are allowed."
            )

        # Check file size (limit: 10MB)
        max_size = getattr(settings, "MAX_DOCUMENT_FILE_SIZE", 10 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size must be under {max_size // (1024 * 1024)}MB."
            )

        return value

    def create(self, validated_data):
        """Populate required model fields (filename, file_size) from the upload."""
        uploaded = validated_data.get("file")
        if uploaded is not None:
            validated_data.setdefault("filename", uploaded.name)
            validated_data.setdefault("file_size", uploaded.size)
        return super().create(validated_data)


class DocumentChunkListSerializer(serializers.ModelSerializer):
    """Serializer for listing document chunks with metadata."""

    document_title = serializers.CharField(source="document.title", read_only=True)
    chunk_text_length = serializers.SerializerMethodField()
    chunk_text_preview = serializers.SerializerMethodField()

    class Meta:
        model = DocumentChunk
        fields = [
            "chunk_index", "page_number", "page_start", "page_end",
            "section_heading", "char_count", "token_count", "embedding_status",
            "created_at", "document_title", "chunk_text_length", "chunk_text_preview"
        ]

    def get_chunk_text_length(self, obj):
        return int(getattr(obj, "char_count", 0) or len(obj.chunk_text or ""))

    def get_chunk_text_preview(self, obj):
        text = (obj.chunk_text or "").strip().replace("\n", " ")
        return text[:280] + ("..." if len(text) > 280 else "")