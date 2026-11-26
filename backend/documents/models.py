from django.db import models, transaction
from django.core.exceptions import ValidationError
import json
import logging

from accounts.models import CustomUser

logger = logging.getLogger(__name__)


def _cleanup_stored_file(file_name, storage):
    if not file_name or not storage:
        return
    try:
        if storage.exists(file_name):
            storage.delete(file_name)
    except Exception:
        logger.exception("Failed to cleanup document file from storage (name=%s)", file_name)


def validate_vector_dimensions(value):
    """Validate that a vector has exactly 3072 dimensions."""
    if value is not None:
        if isinstance(value, (list, tuple)):
            if len(value) != 3072:
                raise ValidationError(
                    f"Vector must have exactly 3072 dimensions, got {len(value)}"
                )
        elif isinstance(value, str):
            try:
                parsed = json.loads(value)
                if len(parsed) != 3072:
                    raise ValidationError(
                        f"Vector must have exactly 3072 dimensions, got {len(parsed)}"
                    )
            except json.JSONDecodeError:
                raise ValidationError("Invalid vector format")


class VectorField(models.JSONField):
    """
    Custom Django Field that ensures vector embeddings have 3072 dimensions.
    
    Stores as JSONB in PostgreSQL, with pgvector compatibility:
    - When pgvector extension is available: embedding::vector for SQL operations
    - Cosine distance: 1 - (embedding <=> query_embedding)
    - Fallback: Python cosine similarity via vector.similarity.cosine_similarity()
    """
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', [0.0] * 3072)
        kwargs.setdefault('help_text', 'Vector embedding as JSON list of 3072 floats')
        super().__init__(*args, **kwargs)
    
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop('help_text', None)
        return name, path, args, kwargs
    
    def get_prep_value(self, value):
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            if len(value) != 3072:
                raise ValidationError(
                    f"Vector must have exactly 3072 dimensions, got {len(value)}"
                )
            return json.dumps(value)
        if isinstance(value, str):
            return value
        return json.dumps(list(value))
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if len(parsed) == 3072:
                    return parsed
            except (json.JSONDecodeError, ValidationError):
                pass
        return super().from_db_value(value, expression, connection)


class DocumentQuerySet(models.QuerySet):
    def delete(self):
        to_delete = list(self.only("file"))
        result = super().delete()
        for doc in to_delete:
            file_name = getattr(getattr(doc, "file", None), "name", None)
            storage = getattr(getattr(doc, "file", None), "storage", None)

            def _do_cleanup(fn=file_name, st=storage):
                _cleanup_stored_file(fn, st)

            transaction.on_commit(_do_cleanup)
        return result


class Document(models.Model):
    """HR Policy document uploaded by HR Admin."""
    STATUS_CHOICES = [
        ("started", "Started"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("ready", "Ready"),
        ("error", "Error"),
    ]
    STAGE_CHOICES = [
        ("uploaded", "PDF uploaded"),
        ("started", "Processing started"),
        ("extracting", "Text extraction"),
        ("chunking", "Text chunking"),
        ("embedding", "Embedding generation"),
        ("storing", "Embedding storage"),
        ("completed", "Completed"),
        ("ready", "Ready for RAG"),
        ("error", "Error"),
    ]

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="hr_policies/")
    uploaded_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="uploaded_documents"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="started")
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    page_count = models.IntegerField(default=0, help_text="Number of pages in PDF")
    extracted_characters = models.PositiveIntegerField(default=0, help_text="Normalized extracted text characters")
    extracted_tokens = models.PositiveIntegerField(default=0, help_text="Estimated tokens for normalized extracted text")
    extraction_tokenizer = models.CharField(max_length=64, blank=True, default="", help_text="Tokenizer used for extracted/chunk token estimates")
    processing_error = models.TextField(blank=True, default="")
    processing_progress = models.PositiveSmallIntegerField(default=0)
    processing_stage = models.CharField(max_length=30, choices=STAGE_CHOICES, default="uploaded")
    processing_stage_detail = models.CharField(max_length=255, blank=True, default="")
    total_chunks = models.PositiveIntegerField(default=0)
    processed_chunks = models.PositiveIntegerField(default=0)
    processing_attempt = models.PositiveIntegerField(default=0)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    objects = DocumentQuerySet.as_manager()

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "HR Policy Document"
        verbose_name_plural = "HR Policy Documents"

    def __str__(self):
        return f"{self.title} ({self.uploaded_at.strftime('%Y-%m-%d')})"

    @property
    def file_path(self):
        return self.file.url

    def delete(self, *args, **kwargs):
        file_name = getattr(self.file, "name", None)
        storage = getattr(self.file, "storage", None)
        result = super().delete(*args, **kwargs)

        def _do_cleanup(fn=file_name, st=storage):
            _cleanup_stored_file(fn, st)

        transaction.on_commit(_do_cleanup)
        return result


class DocumentChunk(models.Model):
    """Text chunks from HR policy documents with embeddings for RAG."""
    EMBEDDING_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("embedded", "Embedded"),
        ("failed", "Failed"),
    ]

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="chunks"
    )
    chunk_index = models.IntegerField()
    chunk_text = models.TextField()
    page_number = models.IntegerField(help_text="Legacy start page for compatibility")
    page_start = models.PositiveIntegerField(default=1)
    page_end = models.PositiveIntegerField(default=1)
    char_count = models.PositiveIntegerField(default=0)
    token_count = models.PositiveIntegerField(default=0)
    section_heading = models.CharField(max_length=255, blank=True, default="")
    embedding_status = models.CharField(max_length=20, choices=EMBEDDING_STATUS_CHOICES, default="embedded")
    embedding = models.JSONField(
        validators=[validate_vector_dimensions],
        help_text="Vector embedding as JSON list of 3072 floats. "
                  "For pgvector SQL: use ::vector cast. "
                  "For Python: use cosine_similarity() from vector.similarity."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["chunk_index"]
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"

    def __str__(self):
        end = self.page_end or self.page_start or self.page_number
        start = self.page_start or self.page_number
        page_label = f"p.{start}" if start == end else f"pp.{start}-{end}"
        return f"Chunk {self.chunk_index} of {self.document.title} ({page_label})"